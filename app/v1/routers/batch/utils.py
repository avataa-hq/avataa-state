import csv
import io
import math

import pandas as pd
from sqlalchemy import select, func, update, desc
from sqlalchemy.ext.asyncio import AsyncSession
from pandas import DataFrame

from v1.database.database import SQLALCHEMY_LIMIT
from v1.database.schemas import KPIValue, KPI
from v1.models.kpi_values import KPIValuesStates
from v1.utils.val_type_serializers import get_serializer_func_for_kpi
from sqlalchemy import and_, or_
from datetime import datetime
from v1.models.kpi_values import KPIValuesStatesPossibleToCreate
from sqlalchemy.orm import selectinload

from v1.utils.val_type_validators import get_value_validate_funct_for_kpi


def get_csv_delimiter(file_data: bytes):
    """Returns csv delimiter"""
    with io.StringIO(file_data.decode("utf-8")) as data:
        sniffer = csv.Sniffer()
        delimiter = sniffer.sniff(data.readline()).delimiter
    return delimiter


CONTENT_TYPES_PANDAS_READER = {
    "text/csv": pd.read_csv,
    "application/vnd.ms-excel": pd.read_csv,
    "application/msexcel": pd.read_excel,
    "application/x-msexcel": pd.read_excel,
    "application/x-ms-excel": pd.read_excel,
    "application/x-excel": pd.read_excel,
    "application/x-dos_ms_excel": pd.read_excel,
    "application/xls": pd.read_excel,
    "application/x-xls": pd.read_excel,
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": pd.read_excel,
}


def get_pandas_file_reader_or_raise_httperror(file_mime_type):
    """Returns pandas reader function for particular file_mime_type, otherwise raises error."""
    pandas_reader = CONTENT_TYPES_PANDAS_READER.get(file_mime_type)
    if pandas_reader:
        return pandas_reader
    else:
        raise ValueError(
            f"File with MIME type = {file_mime_type} does not supported."
            f"Allowed MIME types {list(CONTENT_TYPES_PANDAS_READER)}"
        )


async def save_kpi_values_from_data_frame(df: DataFrame, session: AsyncSession):
    """Creates KPI Values from DataFrame data"""
    MAX_UPDATE_PER_STEP = 7500
    MAX_KPI_VALUE_PER_STEP = 32000

    kpi_ids = {int(kpi_id) for kpi_id in df["kpi_id"].unique()}
    stmt = select(KPI).where(KPI.id.in_(kpi_ids))
    kpis = await session.execute(stmt)
    kpis = kpis.scalars().all()

    cache_serializer_by_kpi = {
        kpi.id: get_serializer_func_for_kpi(kpi.val_type, kpi.multiple)
        for kpi in kpis
    }

    for index, row in df.iterrows():
        kpi_id = int(row.kpi_id)
        kpi_value = KPIValue(
            kpi_id=kpi_id,
            object_id=int(row.object_id),
            value=row.value,
            granularity_id=int(row.granularity_id),
            record_time=datetime.fromisoformat(row.record_time),
            state=row.state,
        )

        serializer = cache_serializer_by_kpi.get(kpi_id)
        kpi_value.serialize_before_save(serializer)
        session.add(kpi_value)

        if index % 10000 == 0:
            await session.flush()
    await session.flush()

    # change last kpi_value for particular kpi and object_id with state 'historical' to state 'current'
    df_to_check = df[["kpi_id", "object_id", "granularity_id", "state"]]
    df_to_check = df_to_check[
        df_to_check["state"] == KPIValuesStates.HISTORICAL.value
    ]

    if not df_to_check.empty:
        data = df_to_check.groupby(["kpi_id", "object_id", "granularity_id"])
        where_condition_current = []

        where_condition_historical = []

        for x in data:
            kp_id, object_id, granularity_id = (
                int(x[0][0]),
                int(x[0][1]),
                int(x[0][2]),
            )
            where_condition_current.append(
                and_(
                    KPIValue.kpi_id == kp_id,
                    KPIValue.object_id == object_id,
                    KPIValue.granularity_id == granularity_id,
                    KPIValue.state == KPIValuesStates.CURRENT.value,
                )
            )

            where_condition_historical.append(
                and_(
                    KPIValue.kpi_id == kp_id,
                    KPIValue.object_id == object_id,
                    KPIValue.granularity_id == granularity_id,
                    KPIValue.state == KPIValuesStates.HISTORICAL.value,
                )
            )

        steps = math.ceil(len(where_condition_current) / MAX_UPDATE_PER_STEP)

        for step in range(steps):
            start = step * MAX_UPDATE_PER_STEP
            end = start + MAX_UPDATE_PER_STEP

            step_where_conditions = where_condition_current[start:end]

            stmt = select(KPIValue).where(or_(*step_where_conditions))
            step_kpi_values = await session.execute(stmt)
            step_kpi_values = step_kpi_values.scalars().all()

            for step_kpi_v in step_kpi_values:
                step_kpi_v.state = KPIValuesStates.HISTORICAL.value
                session.add(step_kpi_v)
            await session.flush()

        all_kpi_value_id_to_update = list()
        steps = math.ceil(len(where_condition_historical) / MAX_UPDATE_PER_STEP)
        for step in range(steps):
            start = step * MAX_UPDATE_PER_STEP
            end = start + MAX_UPDATE_PER_STEP

            step_where_condition_historical = where_condition_historical[
                start:end
            ]

            stmt = (
                select(
                    KPIValue.kpi_id,
                    KPIValue.object_id,
                    KPIValue.granularity_id,
                    func.max(KPIValue.record_time),
                    func.max(KPIValue.id),
                )
                .where(or_(*step_where_condition_historical))
                .group_by(
                    KPIValue.kpi_id, KPIValue.object_id, KPIValue.granularity_id
                )
            )

            step_kpi_value_id_to_update = await session.execute(stmt)
            step_kpi_value_id_to_update = step_kpi_value_id_to_update.all()

            all_kpi_value_id_to_update.extend(
                [item[4] for item in step_kpi_value_id_to_update]
            )

        steps = math.ceil(
            len(all_kpi_value_id_to_update) / MAX_KPI_VALUE_PER_STEP
        )
        for step in range(steps):
            start = step * MAX_KPI_VALUE_PER_STEP
            end = start + MAX_KPI_VALUE_PER_STEP

            step_kpi_value_id_to_update = all_kpi_value_id_to_update[start:end]

            stmt = select(KPIValue).where(
                KPIValue.id.in_(step_kpi_value_id_to_update)
            )
            step_kpi_values = await session.execute(stmt)
            step_kpi_values = step_kpi_values.scalars().all()

            for kpi_value in step_kpi_values:
                kpi_value.state = KPIValuesStates.CURRENT.value
                session.add(kpi_value)

            await session.flush()
    await session.commit()


def validate_int_from_df(iteration: int, column_name: str, value: str):
    try:
        converted_value = int(value)
    except BaseException:
        raise ValueError(
            f"Error in column - {column_name}, line - {iteration + 1} "
            f"invalid value - {value}. "
            f"The values of the {column_name} column must be integers. "
        )
    if float(value) != float(converted_value):
        raise ValueError(
            f"Error in column - {column_name}, line - {iteration + 1} "
            f"invalid value - {value}. "
            f"The values of the {column_name} column must be integers. "
        )
    return converted_value


def validate_enum_values_from_df(
    iteration: int, column_name: str, value: str, allowed_values: dict
):
    if not allowed_values.get(value):
        raise ValueError(
            f"Error in column - {column_name}, line - {iteration + 1} "
            f"invalid value - {value}. "
            f"Allowed values: {list(allowed_values)}"
        )
    return value


def validate_datetime_from_df(iteration: int, column_name: str, value: str):
    try:
        datetime.fromisoformat(value)
        return value
    except BaseException:
        raise ValueError(
            f"Error in column - {column_name}, line - {iteration + 1} "
            f"invalid value - {value}. "
            f"Datetime value must be in ISO 8601 format."
        )


def validate_kpi_value_from_df(
    iteration: int, kpi_id: str, validator_cache: dict, value: str
):
    kpi_id = int(kpi_id)
    kpi_data = validator_cache.get(kpi_id)
    try:
        kpi_data["validate_func"](value)
    except BaseException:
        raise ValueError(
            f"Error in column - value, line - {iteration + 1} "
            f"invalid value - {value}. "
            f"This value is invalid for KPI with settings:"
            f" id = {kpi_id}, val_type = {kpi_data['val_type']}, "
            f"multiple = {kpi_data['multiple']}."
        )


def validate_granularity_from_df(
    iteration: int, kpi_id: str, granularities_cache: dict, granularity_id: str
):
    kpi_id = int(kpi_id)

    granularity_id = validate_int_from_df(
        iteration=iteration, column_name="granularity_id", value=granularity_id
    )

    if granularities_cache[kpi_id].get(granularity_id) is None:
        raise ValueError(
            f"Error in column - granularity_id, line - {iteration + 1} "
            f"invalid value - {granularity_id}. "
            f"Granularity with id = {granularity_id} "
            f"not founded for KPI with id = {kpi_id}"
        )


async def process_file_data_for_batch_import(df_file_data, session):
    required_columns = {
        "kpi_id",
        "object_id",
        "granularity_id",
        "value",
        "record_time",
        "state",
    }

    allowed_states = {x.value: x.value for x in KPIValuesStatesPossibleToCreate}
    # if csv get delimiter

    columns = list(df_file_data.columns)

    difference = required_columns.difference(columns)
    if difference:
        raise ValueError(f"Missing required columns: {difference}!")

    # validate kpi_id
    kpi_ids = {
        validate_int_from_df(i, "kpi_id", x)
        for i, x in enumerate(df_file_data["kpi_id"])
    }
    stmt = (
        select(KPI)
        .where(KPI.id.in_(kpi_ids))
        .options(selectinload(KPI.granularities))
    )
    kpis = await session.execute(stmt)
    kpis = kpis.scalars().all()

    validator_cache = {
        kpi.id: dict(
            validate_func=get_value_validate_funct_for_kpi(
                kpi.val_type, kpi.multiple
            ),
            val_type=kpi.val_type,
            multiple=kpi.multiple,
        )
        for kpi in kpis
    }

    granularities_cache = {
        kpi.id: {gr.id: True for gr in kpi.granularities} for kpi in kpis
    }

    # check if all kpi exist
    kpi_ids_from_db = set(validator_cache)
    if not kpi_ids == kpi_ids_from_db:
        raise ValueError(
            f"Error in column 'kpi_id'. KPIs with ids: {kpi_ids - kpi_ids_from_db} not exist"
        )

    iter_data = enumerate(
        zip(
            df_file_data["kpi_id"],
            df_file_data["object_id"],
            df_file_data["granularity_id"],
            df_file_data["value"],
            df_file_data["record_time"],
            df_file_data["state"],
        )
    )

    [
        (
            validate_int_from_df(
                iteration=i, column_name="object_id", value=values[1]
            ),
            validate_granularity_from_df(
                iteration=i,
                kpi_id=values[0],
                granularities_cache=granularities_cache,
                granularity_id=values[2],
            ),
            validate_kpi_value_from_df(
                iteration=i,
                kpi_id=values[0],
                validator_cache=validator_cache,
                value=values[3],
            ),
            validate_datetime_from_df(
                iteration=i, column_name="record_time", value=values[4]
            ),
            validate_enum_values_from_df(
                iteration=i,
                column_name="state",
                value=values[5],
                allowed_values=allowed_states,
            ),
        )
        for i, values in iter_data
    ]

    return df_file_data


async def update_state_for_all_objects(df: DataFrame, session: AsyncSession):
    kpi_ids = {
        validate_int_from_df(i, "kpi_id", x) for i, x in enumerate(df["kpi_id"])
    }
    stmt = (
        select(KPI)
        .where(KPI.id.in_(kpi_ids))
        .options(selectinload(KPI.granularities))
    )
    kpis = await session.execute(stmt)
    kpis = kpis.scalars().all()

    kpi_ids = [kpi.id for kpi in kpis]

    # all kpi values state current to historical
    stmt = (
        update(KPIValue)
        .where(
            KPIValue.kpi_id.in_(kpi_ids),
            KPIValue.state == KPIValuesStates.CURRENT.value,
        )
        .values(state=KPIValuesStates.HISTORICAL.value)
    )
    await session.execute(stmt)
    await session.commit()
    print("All current become historical")

    # all kpi values state historical with max datetime become current
    for kpi_id in kpi_ids:
        subq = (
            select(
                KPIValue.id.label("kpi_value_id"),
                func.rank()
                .over(
                    partition_by=(
                        KPIValue.kpi_id,
                        KPIValue.granularity_id,
                        KPIValue.object_id,
                    ),
                    order_by=desc(KPIValue.record_time),
                )
                .label("rank"),
            )
            .where(KPIValue.kpi_id == kpi_id)
            .subquery()
        )
        stmt = (
            select(subq.c.kpi_value_id)
            .where(subq.c.rank == 1)
            .execution_options(yield_per=SQLALCHEMY_LIMIT)
        )

        stream = await session.stream_scalars(stmt)
        async for kpi_data in stream.yield_per(SQLALCHEMY_LIMIT).partitions(
            SQLALCHEMY_LIMIT
        ):
            update_stmt = (
                update(KPIValue)
                .where(KPIValue.id.in_(kpi_data))
                .values(state=KPIValuesStates.CURRENT.value)
            )
            await session.execute(update_stmt)
            await session.flush()
    await session.commit()
    print("All max kpi values  become current")


async def fast_save_kpi_values_from_data_frame_with_reload_status(
    df: DataFrame, session: AsyncSession
):
    """Creates KPI Values from DataFrame data but dont add status current"""

    kpi_ids = {int(kpi_id) for kpi_id in df["kpi_id"].unique()}
    stmt = select(KPI).where(KPI.id.in_(kpi_ids))
    kpis = await session.execute(stmt)
    kpis = kpis.scalars().all()

    cache_serializer_by_kpi = {
        kpi.id: get_serializer_func_for_kpi(kpi.val_type, kpi.multiple)
        for kpi in kpis
    }

    iter_data = enumerate(
        zip(
            df["kpi_id"],
            df["object_id"],
            df["granularity_id"],
            df["record_time"],
            df["state"],
            df["value"],
        )
    )

    for index, row in iter_data:
        kpi_id = int(row[0])
        object_id = int(row[1])
        granularity_id = int(row[2])
        record_time = row[3]
        state = row[4]
        value = row[5]
        kpi_value = KPIValue(
            kpi_id=kpi_id,
            object_id=object_id,
            value=value,
            granularity_id=granularity_id,
            record_time=datetime.fromisoformat(record_time),
            state=state,
        )

        serializer = cache_serializer_by_kpi.get(kpi_id)
        kpi_value.serialize_before_save(serializer)
        session.add(kpi_value)

        if index % 10000 == 0:
            await session.flush()
    await session.commit()

    await update_state_for_all_objects(df, session)
