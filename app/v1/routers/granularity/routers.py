from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from v1.database.database import get_session
from v1.database.schemas import Granularity
from v1.models.granularity import (
    GranularityInfoModel,
    GranularityCreateModel,
    GranularityUpdateModel,
)
from v1.routers.granularity.utils import get_granularity_by_id_or_raise_error
from v1.routers.kpi.utils import get_kpi_by_id_or_raise_error

router = APIRouter(prefix="/granularity", tags=["Granularity"])


@router.get("/", status_code=200, response_model=List[GranularityInfoModel])
async def read_all_granularities(session: AsyncSession = Depends(get_session)):
    stmt = select(Granularity)
    granularities = await session.execute(stmt)
    granularities = granularities.scalars().all()

    return granularities


@router.post("/", status_code=201, response_model=GranularityInfoModel)
async def create_granularity_for_particular_kpi(
    granularity: GranularityCreateModel,
    session: AsyncSession = Depends(get_session),
):
    await get_kpi_by_id_or_raise_error(granularity.kpi_id, session)

    stmt = select(Granularity).where(
        Granularity.kpi_id == granularity.kpi_id,
        Granularity.name == granularity.name,
    )
    granularity_exist = await session.execute(stmt)
    granularity_exist = granularity_exist.scalars().first()
    if granularity_exist:
        raise HTTPException(
            status_code=422,
            detail=f"Granularity named {granularity.name} already exists",
        )

    granularity_to_save = Granularity(
        **granularity.model_dump(exclude_unset=True)
    )
    session.add(granularity_to_save)
    await session.commit()
    await session.refresh(granularity_to_save)

    return granularity_to_save


@router.get(
    "/{granularity_id)", status_code=200, response_model=GranularityInfoModel
)
async def read_granularity_by_id(
    granularity_id: int, session: AsyncSession = Depends(get_session)
):
    res = await get_granularity_by_id_or_raise_error(granularity_id, session)
    return res


@router.delete("/{granularity_id)", status_code=204)
async def delete_granularity_by_id(
    granularity_id: int, session: AsyncSession = Depends(get_session)
):
    res = await get_granularity_by_id_or_raise_error(granularity_id, session)
    await session.delete(res)
    await session.commit()
    return {
        "msg": f"Granularity with id - {granularity_id} has been successfully deleted."
    }


@router.patch(
    "/{granularity_id)", status_code=200, response_model=GranularityInfoModel
)
async def partial_update_granularity_by_id(
    granularity_id: int,
    granularity: GranularityUpdateModel,
    session: AsyncSession = Depends(get_session),
):
    granularity_from_db = await get_granularity_by_id_or_raise_error(
        granularity_id, session
    )

    # check if granularity with new name already exists
    stmt = select(Granularity).where(
        Granularity.name == granularity.name,
        Granularity.kpi_id == granularity_from_db.kpi_id,
    )
    granularity_exist = await session.execute(stmt)
    granularity_exist = granularity_exist.scalars().first()

    if granularity_exist and granularity_exist.id != granularity_from_db.id:
        raise HTTPException(
            status_code=422,
            detail=f"Granularity named {granularity.name} already exists",
        )

    for k, v in granularity.model_dump(exclude_unset=True).items():
        setattr(granularity_from_db, k, v)

    session.add(granularity_from_db)
    await session.commit()
    await session.refresh(granularity_from_db)
    return granularity_from_db
