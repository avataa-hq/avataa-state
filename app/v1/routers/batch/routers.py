import io
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Query, Depends, UploadFile, File, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.background import BackgroundTasks
from starlette.responses import StreamingResponse

from v1.database.database import get_session
from v1.database.schemas import KPIValue
import pandas as pd

from v1.models.kpi import KpiValTypes
from v1.models.kpi_values import KPIValuesStatesPossibleToCreate
from v1.routers.batch.utils import (
    CONTENT_TYPES_PANDAS_READER,
    process_file_data_for_batch_import,
    get_pandas_file_reader_or_raise_httperror,
    get_csv_delimiter,
    update_state_for_all_objects,
    fast_save_kpi_values_from_data_frame_with_reload_status,
)

router = APIRouter(prefix="/batch", tags=["Batch operations"])


@router.post(
    "/kpi_value_import",
    status_code=200,
    description=(
        "Creates KPIValues from file.\n\n"
        f"Allowed MIME types {list(CONTENT_TYPES_PANDAS_READER)}.\n\n"
        "File must contains columns: ['kpi_id', 'object_id', 'granularity_id', 'value', "
        "'record_time', 'state'].\n\n"
        "File columns data format:\n\n"
        "kpi_id: int,\n\n"
        "object_id: int,\n\n"
        "granularity_id: int,\n\n"
        f"value: {[x.value for x in KpiValTypes]},\n\n"
        "record_time: datetime - example 2000-12-12T00:00:00\n\n"
        f"state: {[x.value for x in KPIValuesStatesPossibleToCreate]}\n\n"
    ),
)
async def batch_import(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(),
    session: AsyncSession = Depends(get_session),
):
    file_data = file.file.read()
    pandas_file_reader = get_pandas_file_reader_or_raise_httperror(
        file_mime_type=file.content_type
    )
    additional_data = dict()
    if pandas_file_reader == pd.read_csv:
        delimiter = get_csv_delimiter(file_data)
        additional_data = dict(delimiter=delimiter)

    with io.BytesIO(file_data) as output:
        request_df = pandas_file_reader(output, dtype="str", **additional_data)

    try:
        response_df = await process_file_data_for_batch_import(
            df_file_data=request_df, session=session
        )
    except ValueError as error_message:
        raise HTTPException(status_code=422, detail=str(error_message))

    # if file is valid - save data
    background_tasks.add_task(
        fast_save_kpi_values_from_data_frame_with_reload_status,
        response_df,
        session,
    )
    return {
        "status": "ok",
        "detail": "The file has been uploaded and "
        "will be processed in the background.",
    }


@router.get("/kpi_value_export", status_code=200)
async def batch_export(
    kpi_id: List[int] = Query(default=None),
    object_id: List[int] = Query(default=None),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    session: AsyncSession = Depends(get_session),
):
    where_conditions = []

    if kpi_id:
        where_conditions.append(KPIValue.id.in_(kpi_id))

    if object_id:
        where_conditions.append(KPIValue.object_id.in_(object_id))

    if date_from:
        where_conditions.append(KPIValue.record_time >= date_from)

    if date_to:
        where_conditions.append(KPIValue.record_time <= date_to)

    stmt = (
        select(
            KPIValue.object_id,
            KPIValue.kpi_id,
            KPIValue.granularity_id,
            KPIValue.record_time,
            KPIValue.value,
            KPIValue.state,
            KPIValue.id,
        )
        .where(*where_conditions)
        .order_by(
            KPIValue.object_id,
            KPIValue.kpi_id,
            KPIValue.granularity_id,
            KPIValue.record_time,
        )
    )
    res = await session.execute(stmt)
    res = res.all()

    df = pd.DataFrame(data=res)
    output = io.BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)
    headers = {"Content-Disposition": 'attachment; filename="export_data.csv"'}

    return StreamingResponse(output, headers=headers)


@router.post(
    "/reload_kpi_value_statuses_all",
    status_code=200,
    description=("Reload status for all kpis"),
)
async def update_state(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(),
    session: AsyncSession = Depends(get_session),
):
    file_data = file.file.read()
    pandas_file_reader = get_pandas_file_reader_or_raise_httperror(
        file_mime_type=file.content_type
    )
    additional_data = dict()
    if pandas_file_reader == pd.read_csv:
        delimiter = get_csv_delimiter(file_data)
        additional_data = dict(delimiter=delimiter)

    with io.BytesIO(file_data) as output:
        request_df = pandas_file_reader(output, dtype="str", **additional_data)

    required_columns = {"kpi_id"}
    columns_from_file = set(request_df.columns)
    print(columns_from_file)
    if required_columns.issubset(columns_from_file) is False:
        raise HTTPException(
            status_code=422,
            detail=f"Please add required columns {required_columns}",
        )

    # if file is valid - save data
    background_tasks.add_task(update_state_for_all_objects, request_df, session)
    return {
        "status": "ok",
        "detail": "The file has been uploaded and "
        "will be processed in the background.",
    }
