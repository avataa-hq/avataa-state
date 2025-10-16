from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from v1.database.schemas import KPIValue
from v1.models.kpi_values import KPIValuesStates
from v1.routers.kpi_value.configs import (
    AGGREGATION_CORRESPONDING_TABLE,
    CORRESPONDING_SQL_CAST_TYPE_TABLE,
)


async def get_kpi_value_by_id_or_raise_error(
    kpi_value_id: int, session: AsyncSession
):
    """Returns kpi value instance if kpi value with id = kpi_value_id exists, otherwise raises error."""
    kpi_from_db = await session.get(KPIValue, kpi_value_id)

    if kpi_from_db is None:
        raise HTTPException(
            status_code=404,
            detail=f"KPIValue with id = {kpi_value_id} does not exist!",
        )
    return kpi_from_db


async def get_current_kpi_value_for_particular_kpi(
    kpi_id: int, object_id: int, granularity_id: int, session: AsyncSession
):
    """Returns current kpi_value with state = current, otherwise returns None"""

    stmt = select(KPIValue).where(
        KPIValue.kpi_id == kpi_id,
        KPIValue.object_id == object_id,
        KPIValue.granularity_id == granularity_id,
        KPIValue.state == KPIValuesStates.CURRENT.value,
    )
    res = await session.execute(stmt)
    return res.scalars().first()


def get_aql_aggregation_function(agg_f_name: str):
    """Returns sqlalchemy corresponding aggregation function, otherwise raises error"""
    corresp_aggr_func = AGGREGATION_CORRESPONDING_TABLE.get(agg_f_name)
    if corresp_aggr_func:
        return corresp_aggr_func
    raise NotImplementedError(
        f"Aggregation function does not implemented for key {agg_f_name}"
    )


def get_corresponding_cast_sql_type(kpi_val_type: str):
    """Returns sqlalchemy corresponding cast type, otherwise raises error"""
    corresp_cast_type = CORRESPONDING_SQL_CAST_TYPE_TABLE.get(kpi_val_type)
    if corresp_cast_type:
        return corresp_cast_type
    raise NotImplementedError(
        f"Cast type does not implemented for KPI with value type:  {kpi_val_type}"
    )
