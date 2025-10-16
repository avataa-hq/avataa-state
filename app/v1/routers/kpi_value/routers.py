from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects import postgresql
from sqlalchemy import text
from v1.database.database import get_session
from v1.database.schemas import KPIValue, Granularity
from v1.models.kpi_values import (
    KPIValuesStates,
    KPIValuePlannedModelCreateByKPI,
    KPIValuePlannedModelUpdateByKPI,
    KPIValueHistoricalModelCreateByKPI,
    KPIValueModelInfo,
)
from v1.models.request_models import KPIAggrRequest
from v1.routers.kpi.utils import get_kpi_by_id_or_raise_error
from v1.routers.kpi_value.enum_models import (
    AvailableAggrKPIValTypes,
    AvailableKPIAggregations,
)
from v1.routers.kpi_value.utils import (
    get_kpi_value_by_id_or_raise_error,
    get_current_kpi_value_for_particular_kpi,
    get_aql_aggregation_function,
    get_corresponding_cast_sql_type,
)
from v1.utils.val_type_deserializers import (
    get_deserializer_func_for_kpi,
    get_deserialized_kpi_value_inst,
)
from v1.utils.val_type_serializers import get_serializer_func_for_kpi
from v1.utils.val_type_validators import get_value_validate_funct_for_kpi

router = APIRouter(prefix="/kpi_values")


@router.get(
    "/common/{kpi_id}",
    summary="Read KPI values for particular KPI",
    status_code=200,
    tags=["KPI Values: Common"],
    response_model=List[KPIValueModelInfo],
)
async def read_kpi_values_by_kpi_id(
    kpi_id: int,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    object_id: int = None,
    granularity_id: int = None,
    session: AsyncSession = Depends(get_session),
):
    """Returns KPI values for particular kpi_id"""
    kpi_from_db = await get_kpi_by_id_or_raise_error(kpi_id, session)

    deserializer = get_deserializer_func_for_kpi(
        kpi_from_db.val_type, kpi_from_db.multiple
    )

    where_condition = []
    if date_from is not None:
        where_condition.append(KPIValue.record_time >= date_from)

    if date_to is not None:
        where_condition.append(KPIValue.record_time <= date_to)

    if object_id is not None:
        where_condition.append(KPIValue.object_id == object_id)

    if granularity_id is not None:
        where_condition.append(KPIValue.granularity_id == granularity_id)

    stmt = (
        select(KPIValue)
        .where(KPIValue.kpi_id == kpi_id, *where_condition)
        .order_by(KPIValue.record_time)
    )
    res = await session.execute(stmt)
    res = res.scalars().all()
    res = map(lambda x: get_deserialized_kpi_value_inst(x, deserializer), res)

    return list(res)


@router.delete(
    "/common/kpi_value/{kpi_value_id}",
    summary="Delete KPI value by KPIValue.id",
    status_code=204,
    tags=["KPI Values: Common"],
)
async def delete_kpi_value_by_kpi_value_id(
    kpi_value_id: int, session: AsyncSession = Depends(get_session)
):
    """Deletes KPI value if KPI Value with kpi_value_id exist, otherwise raises error."""

    kpi_value = await get_kpi_value_by_id_or_raise_error(kpi_value_id, session)
    if kpi_value.state == KPIValuesStates.CURRENT.value:
        stmt = select(func.max(KPIValue.record_time)).where(
            KPIValue.kpi_id == kpi_value.kpi_id,
            KPIValue.object_id == kpi_value.object_id,
            KPIValue.granularity_id == kpi_value.granularity_id,
            KPIValue.state != KPIValuesStates.CURRENT.value,
        )
        latest_record_date = await session.execute(stmt)
        latest_record_date = latest_record_date.scalars().first()
        if latest_record_date:
            stmt = select(KPIValue).where(
                KPIValue.kpi_id == kpi_value.kpi_id,
                KPIValue.object_id == kpi_value.object_id,
                KPIValue.state != KPIValuesStates.CURRENT.value,
                KPIValue.granularity_id == kpi_value.granularity_id,
                KPIValue.record_time == latest_record_date,
            )
            latest_record = await session.execute(stmt)
            latest_record = latest_record.scalars().first()
            latest_record.state = KPIValuesStates.CURRENT.value
            session.add(latest_record)

    await session.delete(kpi_value)
    await session.commit()
    return {"msg": f"KPIValue with id = {kpi_value_id} deleted successfully!"}


@router.get(
    "/common/kpi_value/{kpi_value_id}",
    summary="Read KPI value by KPIValue.id",
    status_code=200,
    tags=["KPI Values: Common"],
    response_model=KPIValueModelInfo,
)
async def read_kpi_value_by_kpi_value_id(
    kpi_value_id: int, session: AsyncSession = Depends(get_session)
):
    """Returns KPI value if KPI Value with kpi_value_id exist, otherwise raises error."""

    kpi_value = await get_kpi_value_by_id_or_raise_error(kpi_value_id, session)
    kpi_from_db = await get_kpi_by_id_or_raise_error(kpi_value.kpi_id, session)
    deserializer = get_deserializer_func_for_kpi(
        kpi_from_db.val_type, kpi_from_db.multiple
    )

    return get_deserialized_kpi_value_inst(kpi_value, deserializer)


@router.post(
    "/planned/{kpi_id}",
    summary="Create Planned KPI value for particular KPI",
    status_code=201,
    tags=["KPI Values: Planned"],
    response_model=KPIValueModelInfo,
)
async def create_planned_kpi_value_for_particular_kpi(
    kpi_id: int,
    kpi_value: KPIValuePlannedModelCreateByKPI,
    session: AsyncSession = Depends(get_session),
):
    """Creates KPI value for particular KPI"""
    kpi_from_db = await get_kpi_by_id_or_raise_error(kpi_id, session)

    if kpi_value.granularity_id not in [
        x.id for x in kpi_from_db.granularities
    ]:
        raise HTTPException(
            status_code=422,
            detail=f"KPI with id = {kpi_id} has no "
            f"Granularity with id = {kpi_value.granularity_id}",
        )

    deserializer = get_deserializer_func_for_kpi(
        kpi_from_db.val_type, kpi_from_db.multiple
    )
    serializer = get_serializer_func_for_kpi(
        kpi_from_db.val_type, kpi_from_db.multiple
    )

    validator = get_value_validate_funct_for_kpi(
        kpi_from_db.val_type, kpi_from_db.multiple
    )
    valid_value = validator(kpi_value.value)

    kpi_value_inst = KPIValue(
        kpi_id=kpi_id,
        state=KPIValuesStates.PLANNED.value,
        **kpi_value.model_dump(),
    )
    kpi_value_inst.value = valid_value
    kpi_value_inst.serialize_before_save(serializer)

    session.add(kpi_value_inst)
    await session.commit()
    await session.refresh(kpi_value_inst)

    return get_deserialized_kpi_value_inst(kpi_value_inst, deserializer)


@router.patch(
    "/planned/kpi_value/{kpi_value_id}",
    summary="Update Planned KPI value by KPIValue.id",
    status_code=200,
    tags=["KPI Values: Planned"],
)
async def update_planned_kpi_value_by_kpi_value_id(
    kpi_value_id: int,
    kpi_value: KPIValuePlannedModelUpdateByKPI,
    session: AsyncSession = Depends(get_session),
):
    """Updates KPI value if KPI Value with kpi_value_id exist, otherwise raises error."""

    kpi_value_from_db = await get_kpi_value_by_id_or_raise_error(
        kpi_value_id, session
    )
    kpi_from_db = await get_kpi_by_id_or_raise_error(
        kpi_value_from_db.kpi_id, session
    )

    validator = get_value_validate_funct_for_kpi(
        kpi_from_db.val_type, kpi_from_db.multiple
    )
    serializer = get_serializer_func_for_kpi(
        kpi_from_db.val_type, kpi_from_db.multiple
    )

    for k, v in kpi_value.model_dump(exclude_unset=True).items():
        setattr(kpi_value_from_db, k, v)

    kpi_value_from_db.validate_value(validator)
    kpi_value_from_db.serialize_before_save(serializer)

    session.add(kpi_value_from_db)
    await session.commit()

    deserializer = get_deserializer_func_for_kpi(
        kpi_from_db.val_type, kpi_from_db.multiple
    )

    return get_deserialized_kpi_value_inst(kpi_value_from_db, deserializer)


@router.post(
    "/historical/{kpi_id}",
    summary="Create Historical KPI value for particular KPI",
    status_code=201,
    tags=["KPI Values: Historical"],
)
async def create_historical_kpi_value_for_particular_kpi(
    kpi_id: int,
    kpi_value: KPIValueHistoricalModelCreateByKPI,
    session: AsyncSession = Depends(get_session),
):
    """Creates KPI value for particular KPI"""
    kpi_from_db = await get_kpi_by_id_or_raise_error(kpi_id, session)

    if kpi_value.granularity_id not in [
        x.id for x in kpi_from_db.granularities
    ]:
        raise HTTPException(
            status_code=422,
            detail=f"KPI with id = {kpi_id} has no "
            f"Granularity with id = {kpi_value.granularity_id}",
        )

    deserializer = get_deserializer_func_for_kpi(
        kpi_from_db.val_type, kpi_from_db.multiple
    )
    serializer = get_serializer_func_for_kpi(
        kpi_from_db.val_type, kpi_from_db.multiple
    )

    validator = get_value_validate_funct_for_kpi(
        kpi_from_db.val_type, kpi_from_db.multiple
    )
    valid_value = validator(kpi_value.value)

    kpi_value_inst = KPIValue(
        kpi_id=kpi_id,
        state=KPIValuesStates.CURRENT.value,
        **kpi_value.model_dump(),
    )
    kpi_value_inst.value = valid_value
    kpi_value_inst.serialize_before_save(serializer)

    current_kpi_value = await get_current_kpi_value_for_particular_kpi(
        kpi_id=kpi_value_inst.kpi_id,
        object_id=kpi_value_inst.object_id,
        granularity_id=kpi_value.granularity_id,
        session=session,
    )
    if current_kpi_value:
        current_kpi_value.state = KPIValuesStates.HISTORICAL.value
        session.add(current_kpi_value)

    session.add(kpi_value_inst)

    await session.commit()
    await session.refresh(kpi_value_inst)

    return get_deserialized_kpi_value_inst(kpi_value_inst, deserializer)


@router.post(
    "/aggregation_data",
    summary="Returns aggregated KPI values for special object_ids",
    status_code=200,
    tags=["KPI Values: Aggregation"],
)
async def get_aggregated_data_for_special_object_ids(
    aggr_request: KPIAggrRequest, session: AsyncSession = Depends(get_session)
):
    """Returns aggregated KPI values for special object_ids"""
    kpi_from_db = await get_kpi_by_id_or_raise_error(
        aggr_request.kpi_id, session
    )

    available_val_types = {x.value for x in AvailableAggrKPIValTypes}

    if kpi_from_db.val_type not in available_val_types:
        raise HTTPException(
            status_code=422,
            detail=f"Value type '{kpi_from_db.val_type}' is not available for aggregation operations",
        )
    if kpi_from_db.multiple:
        raise HTTPException(
            status_code=422,
            detail="Multiple value type is not available for aggregation operations",
        )
    try:
        sql_cast_type = get_corresponding_cast_sql_type(kpi_from_db.val_type)
    except NotImplementedError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # check granularity id
    stmt = select(Granularity).where(
        Granularity.id == aggr_request.granularity_id,
        Granularity.kpi_id == aggr_request.kpi_id,
    )
    granularity = await session.execute(stmt)
    granularity = granularity.scalars().first()

    if not granularity:
        raise HTTPException(
            status_code=404,
            detail=f"Granularity with id = {aggr_request.granularity_id} not founded",
        )

    where_conditions = [
        KPIValue.granularity_id == aggr_request.granularity_id,
        KPIValue.object_id.in_(aggr_request.object_ids),
    ]
    if aggr_request.date_from is not None:
        where_conditions.append(KPIValue.record_time >= aggr_request.date_from)

    if aggr_request.date_to is not None:
        where_conditions.append(KPIValue.record_time <= aggr_request.date_to)

    if (
        aggr_request.aggregation_type
        == AvailableKPIAggregations.MOST_FREQUENT.value
    ):
        stmt = (
            select(
                KPIValue.object_id,
                KPIValue.value,
                func.count(KPIValue.value).label("count_val"),
            )
            .where(*where_conditions)
            .group_by(KPIValue.object_id, KPIValue.value)
            .order_by(
                KPIValue.object_id.asc(), func.count(KPIValue.value).desc()
            )
            .distinct(KPIValue.object_id)
        )
        compiled_stmt = text(
            str(
                stmt.compile(
                    compile_kwargs={"literal_binds": True},
                    dialect=postgresql.dialect(),
                )
            )
        )
        res = await session.execute(compiled_stmt)
        res = res.all()
        res = {x[0]: x[1] if x[1] else 0 for x in res}

    else:
        try:
            aggr_func = get_aql_aggregation_function(
                aggr_request.aggregation_type
            )
        except NotImplementedError as e:
            raise HTTPException(status_code=422, detail=str(e))

        stmt = (
            select(
                KPIValue.object_id,
                aggr_func(KPIValue.value.cast(sql_cast_type)),
            )
            .where(*where_conditions)
            .group_by(KPIValue.object_id)
        )
        res = await session.execute(stmt)
        res = res.all()
        res = {x[0]: x[1] if x[1] else 0 for x in res}

    return res
