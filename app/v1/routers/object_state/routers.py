from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from v1.database.database import get_session
from v1.database.schemas import KPIValue, KPI
from v1.models.kpi_values import KPIValuesStates
from v1.utils.val_type_deserializers import get_deserializer_func_for_kpi

router = APIRouter(prefix="/object_state", tags=["Object State"])


@router.get("/current/{object_id}")
async def read_current_object_state(
    object_id: int, session: AsyncSession = Depends(get_session)
):
    """Returns all kpi_values with state = current for particular object_id"""

    stmt = (
        select(KPIValue, KPI)
        .join(KPI, KPIValue.kpi_id == KPI.id)
        .where(
            KPIValue.object_id == object_id,
            KPIValue.state == KPIValuesStates.CURRENT.value,
        )
    )

    res = await session.execute(stmt)
    res = res.all()

    if len(res) == 0:
        raise HTTPException(
            status_code=404,
            detail=f"KPIValues for object_id = {object_id} not exist.",
        )

    object_state = dict()
    object_state["object_id"] = object_id

    for kpi_value, kpi in res:
        record = object_state.setdefault(kpi.name, [])

        deserializer = get_deserializer_func_for_kpi(kpi.val_type, kpi.multiple)
        record.append(
            dict(
                granularity_id=kpi_value.granularity_id,
                value=deserializer(kpi_value.value),
            )
        )

    return object_state
