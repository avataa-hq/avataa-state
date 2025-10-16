from typing import List

from fastapi import APIRouter, Depends, HTTPException, Body

from sqlalchemy.ext.asyncio import AsyncSession

from exception_manager.manager import (
    NotFoundError,
    KPIUpdateError,
    KPIRelatedValidationError,
    ValidationError,
)
from services.kpi_services.service import (
    get_all_kpis_with_related,
    create_new_kpi,
    get_related_kpis_with_tmo_id,
    delete_kpi_instance_by_id,
    update_kpi_instance,
    get_kpi_by_tmo_id,
)
from v1.database.database import get_session
from v1.database.schemas import KPI
from v1.models.granularity import GranularityInfoModel
from v1.models.kpi import (
    KPIModelInfo,
    KPIModelCreate,
    KPIModelPartialUpdate,
    RelatedKPIsWithTMO,
)
from v1.routers.kpi.utils import (
    get_kpi_by_id_or_raise_custom_error,
    get_kpi_with_related,
    get_list_of_kpi_with_related,
)
from v1.routers.palette.utils import create_default_palette_for_kpis

router = APIRouter(prefix="/kpi", tags=["KPI"])


@router.get("", status_code=200, response_model=List[KPIModelInfo])
async def read_all_kpis(session: AsyncSession = Depends(get_session)):
    """Returns all KPIs"""
    kpis_data = await get_all_kpis_with_related(session=session)
    return kpis_data


@router.post("", status_code=201, response_model=KPIModelInfo)
async def create_kpi(
    kpi: KPIModelCreate, session: AsyncSession = Depends(get_session)
):
    """Creates KPI"""
    try:
        new_kpi = await create_new_kpi(session=session, main_kpi=kpi)
        if new_kpi:
            wrong_kpi_ids = await create_default_palette_for_kpis(
                kpis=[KPI(**new_kpi)]
            )

            if wrong_kpi_ids:
                raise HTTPException(
                    status_code=503,
                    detail="Its impossible to set palette for this KPI",
                )

        await session.commit()

    except NotFoundError as error_message:
        raise HTTPException(status_code=422, detail=str(error_message))

    except KPIRelatedValidationError as error_message:
        raise HTTPException(status_code=422, detail=str(error_message))
    return new_kpi


@router.get("/{kpi_id}", status_code=200)
async def read_kpi_by_id(
    kpi_id: int, session: AsyncSession = Depends(get_session)
):
    """Returns kpi instance by kpi_id, otherwise raises error."""
    try:
        result_kpi = await get_kpi_with_related(session=session, kpi_id=kpi_id)

    except NotFoundError as error_message:
        raise HTTPException(status_code=422, detail=str(error_message))
    return result_kpi


@router.delete("/{kpi_id}", status_code=204)
async def delete_kpi_by_id(
    kpi_id: int, session: AsyncSession = Depends(get_session)
):
    """Returns kpi instance by kpi_id, otherwise raises error."""
    try:
        await delete_kpi_instance_by_id(session=session, kpi_id=kpi_id)

    except NotFoundError as message_error:
        raise HTTPException(status_code=422, detail=str(message_error))

    return {"msg": f"KPI with id = {kpi_id} deleted successfully"}


@router.patch("/{kpi_id}", status_code=200)
async def partial_kpi_update(
    kpi_id: int,
    kpi: KPIModelPartialUpdate,
    force: bool = False,
    session: AsyncSession = Depends(get_session),
):
    """Updates KPI instance."""
    try:
        kpi_inst = await update_kpi_instance(
            session=session, kpi_id=kpi_id, kpi=kpi, force=force
        )

    except (NotFoundError, KPIUpdateError, ValidationError) as message_error:
        raise HTTPException(status_code=422, detail=str(message_error))

    return kpi_inst


@router.get(
    "/{kpi_id}/granularity",
    status_code=200,
    response_model=List[GranularityInfoModel],
)
async def read_kpi_granularities(
    kpi_id: int, session: AsyncSession = Depends(get_session)
):
    """Returns kpi granularities by kpi_id, otherwise raises error."""
    try:
        kpi_inst = await get_kpi_by_id_or_raise_custom_error(kpi_id, session)

    except NotFoundError as message_error:
        raise HTTPException(status_code=422, detail=str(message_error))

    return kpi_inst.granularities


@router.get(
    "/for_special_object_type/{object_type_id}",
    status_code=200,
    response_model=List[KPIModelInfo],
)
async def read_kpi_for_special_object_type(
    object_type_id: int, session: AsyncSession = Depends(get_session)
):
    """Returns kpi for special object_type_id by kpi_id."""
    list_of_kpi = await get_kpi_by_tmo_id(
        session=session, object_type_id=object_type_id, add_related_to_kpi=True
    )
    return list_of_kpi


@router.post(
    "/get_kpi_by_ids", status_code=200, response_model=List[KPIModelInfo]
)
async def read_kpi_by_ids(
    kpi_ids: List[int] = Body(), session: AsyncSession = Depends(get_session)
):
    """Returns kpi for by kpi_ids."""
    try:
        kpis = await get_list_of_kpi_with_related(
            session=session, kpi_ids=kpi_ids
        )

    except NotFoundError as error_message:
        raise HTTPException(status_code=422, detail=str(error_message))

    return kpis


@router.get(
    "/get_related_kpi_tmos/{kpi_id}",
    status_code=200,
    response_model=RelatedKPIsWithTMO,
)
async def get_related_kpi_tmos(
    kpi_id: int, session: AsyncSession = Depends(get_session)
):
    related_kpis_with_tmo_id = await get_related_kpis_with_tmo_id(
        session=session, main_kpi_id=kpi_id
    )
    return related_kpis_with_tmo_id
