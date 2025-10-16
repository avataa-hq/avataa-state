from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from exception_manager.manager import NotFoundError, KPIUpdateError
from v1.database.database import get_chunked_values_by_sqlalchemy_limit
from v1.database.schemas import KPI, KPIValue, possible_brach_types
from v1.models.kpi import (
    KPIModelCreate,
    KPIModelPartialUpdate,
    RelatedKPIsWithTMO,
)
from v1.routers.kpi.utils import (
    get_kpi_by_id_or_raise_custom_error,
    add_related_kpis_to_main,
    update_kpi_related_kpis,
    get_list_of_kpis,
    get_related_kpis_by_list_of_kpi,
    create_related_kpis,
    validate_relative_kpis,
    create_links,
    validate_links,
    update_kpi_links,
)
from v1.utils.val_type_deserializers import get_deserializer_func_for_kpi
from v1.utils.val_type_serializers import get_serializer_func_for_kpi
from v1.utils.val_type_validators import get_value_validate_funct_for_kpi


async def get_all_kpis_with_related(session: AsyncSession):
    response = []
    kpis = await session.execute(
        select(KPI).options(selectinload(KPI.related_kpis))
    )
    kpis = kpis.scalars().all()

    for kpi in kpis:
        temp_kpi = kpi.__dict__

        temp_kpi["related_kpis"] = [related.id for related in kpi.related_kpis]
        response.append(temp_kpi)

    return response


async def get_all_kpis_without_related(session: AsyncSession):
    kpis = await session.execute(select(KPI))
    kpis = kpis.scalars().all()

    return kpis


async def create_new_kpi(
    session: AsyncSession, main_kpi: KPIModelCreate
) -> dict:
    stmt = select(KPI).where(
        KPI.name == main_kpi.name, KPI.object_type == main_kpi.object_type
    )
    existing_kpi = await session.execute(stmt)
    existing_kpi = existing_kpi.scalars().first()
    if existing_kpi:
        raise NotFoundError(
            f"KPI with name '{main_kpi.name}' and object_type "
            f"'{main_kpi.object_type}' already exists!"
        )

    if not main_kpi.branch or main_kpi.branch not in possible_brach_types:
        raise HTTPException(
            status_code=422,
            detail=f"Values for branch can be only: {possible_brach_types}",
        )

    if main_kpi.related_kpis:
        await validate_relative_kpis(
            session=session,
            related_kpis=set(main_kpi.related_kpis),
            main_kpi=main_kpi,
        )

    await validate_links(session=session, main_kpi=main_kpi)

    new_kpi = KPI(
        name=main_kpi.name,
        description=main_kpi.description,
        label=main_kpi.label,
        branch=main_kpi.branch,
        val_type=main_kpi.val_type,
        multiple=main_kpi.multiple,
        object_type=main_kpi.object_type,
        group=main_kpi.group,
        parent_kpi=main_kpi.parent_kpi,
        child_kpi=main_kpi.child_kpi,
    )

    session.add(new_kpi)
    await session.flush()

    related_kpis = []
    if main_kpi.related_kpis:
        related_kpis = await create_related_kpis(
            session=session,
            main_kpi=new_kpi,
            related_kpis=set(main_kpi.related_kpis),
        )

    await create_links(session=session, main_kpi=new_kpi)

    new_kpi = new_kpi.__dict__
    new_kpi["related_kpis"] = related_kpis
    del new_kpi["_sa_instance_state"]

    return new_kpi


async def delete_kpi_instance_by_id(session: AsyncSession, kpi_id: int):
    kpi_inst = await get_kpi_by_id_or_raise_custom_error(kpi_id, session)

    for granularity in kpi_inst.granularities:
        await session.delete(granularity)

    await session.delete(kpi_inst)
    await session.commit()


async def update_kpi_instance(
    session: AsyncSession, kpi_id: int, kpi: KPIModelPartialUpdate, force: bool
):
    kpi_inst = await get_kpi_by_id_or_raise_custom_error(kpi_id, session)

    update_data = kpi.model_dump(exclude_unset=True)

    errors = []
    if (
        update_data.get("val_type")
        and update_data.get("val_type") != kpi_inst.val_type
    ):
        if force:
            validator = get_value_validate_funct_for_kpi(
                kpi.val_type, kpi_inst.multiple
            )
            deserializer = get_deserializer_func_for_kpi(
                kpi_inst.val_type, kpi_inst.multiple
            )
            serializer = get_serializer_func_for_kpi(
                kpi.val_type, kpi_inst.multiple
            )

            stmt = select(KPIValue).where(KPIValue.kpi_id == kpi_id)
            kpi_values = await session.execute(stmt)
            kpi_values = kpi_values.scalars().all()

            for kpi_value in kpi_values:
                try:
                    value = validator(deserializer(kpi_value.value))
                except HTTPException:
                    await session.delete(kpi_value)
                else:
                    kpi_value.value = serializer(value)
                    session.add(kpi_value)

        else:
            errors.append(
                f"You are trying to change KPI val_type. Current val_type ='{kpi_inst.val_type}'. "
                f"All KPI values that fail validation will be deleted. To make changes, send request "
                f"with force = True"
            )
    if errors:
        raise KPIUpdateError(errors)

    if not kpi.branch or kpi.branch not in possible_brach_types:
        raise HTTPException(
            status_code=422,
            detail=f"Values for branch can be only: {possible_brach_types}",
        )

    if update_data.get("related_kpis"):
        related_kpis = update_data.pop("related_kpis")
    else:
        related_kpis = []

    await validate_links(session=session, main_kpi=kpi, kpi_id=kpi_id)

    for k, v in update_data.items():
        setattr(kpi_inst, k, v)

    session.add(kpi_inst)
    await session.flush()

    if related_kpis:
        related_kpis = await update_kpi_related_kpis(
            session=session, main_kpi=kpi_inst, related_kpis=set(related_kpis)
        )

    await update_kpi_links(session=session, kpi_id=kpi_id, main_kpi=kpi_inst)

    await session.commit()
    kpi_inst.__dict__["related_kpis"] = related_kpis

    return kpi_inst


async def get_kpi_by_tmo_id(
    session: AsyncSession, object_type_id: int, add_related_to_kpi: bool
):
    list_of_kpi = []
    stmt = (
        select(KPI)
        .where(KPI.object_type == object_type_id)
        .options(selectinload(KPI.related_kpis))
    )
    kpis = await session.execute(stmt)
    kpis = kpis.scalars().all()
    if add_related_to_kpi:
        for kpi in kpis:
            temp_kpi = kpi.__dict__
            temp_kpi["related_kpis"] = (
                [related.id for related in kpi.related_kpis]
                if kpi.related_kpis
                else []
            )
            list_of_kpi.append(temp_kpi)

    else:
        for kpi in kpis:
            temp_kpi = kpi.__dict__
            del temp_kpi["related_kpis"]
            list_of_kpi.append(temp_kpi)

    return list_of_kpi


async def get_kpis_by_list_of_ids(
    session: AsyncSession, kpi_id_list: list[int], add_related_to_kpi: bool
):
    kpis = await get_list_of_kpis(
        session=session, requested_kpi_ids=set(kpi_id_list)
    )
    if add_related_to_kpi:
        kpis = await add_related_kpis_to_main(session=session, main_kpis=kpis)
    return kpis


async def get_related_kpis_with_tmo_id(session: AsyncSession, main_kpi_id: int):
    exists_kpi = await session.execute(select(KPI).where(KPI.id == main_kpi_id))
    exists_kpi = exists_kpi.scalars().all()

    response = RelatedKPIsWithTMO(related_kpis=[])
    if exists_kpi:
        kpi_with_related = await get_related_kpis_by_list_of_kpi(
            session=session, kpi_ids=[main_kpi_id]
        )

        if kpi_with_related:
            kpi_with_related = get_chunked_values_by_sqlalchemy_limit(
                kpi_with_related[main_kpi_id]
            )
            kpi_and_object_data = []
            for chunk in kpi_with_related:
                temp = await session.execute(
                    select(KPI).where(KPI.id.in_(chunk))
                )
                kpi_and_object_data.extend(temp.scalars().all())
            response = RelatedKPIsWithTMO(
                related_kpis=[
                    {"kpi_id": kpi.id, "object_type_id": kpi.object_type}
                    for kpi in kpi_and_object_data
                ]
            )

    return response
