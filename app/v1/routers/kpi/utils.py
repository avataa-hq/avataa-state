from collections import defaultdict
from typing import List

from fastapi import HTTPException

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from exception_manager.manager import (
    NotFoundError,
    KPIRelatedValidationError,
    KPILinkValidationError,
)
from v1.database.database import get_chunked_values_by_sqlalchemy_limit
from v1.database.schemas import KPI, RelatedKPI
from v1.models.kpi import KPIModelCreate, KPIModelPartialUpdate


async def get_kpi_by_id_or_raise_error(
    kpi_id: int, session: AsyncSession
) -> KPI:
    """Returns kpi instance if kpi with id = kpi_id exists, otherwise raises error."""
    stmt = (
        select(KPI)
        .where(KPI.id == kpi_id)
        .options(selectinload(KPI.granularities))
    )
    kpi_from_db = await session.execute(stmt)
    kpi_from_db = kpi_from_db.scalars().first()

    if kpi_from_db is None:
        raise HTTPException(
            status_code=422, detail=f"KPI with id = {kpi_id} does not exist!"
        )
    return kpi_from_db


async def get_kpi_by_id_or_raise_custom_error(
    kpi_id: int, session: AsyncSession
) -> KPI:
    """Returns kpi instance if kpi with id = kpi_id exists, otherwise raises custom error."""
    stmt = (
        select(KPI)
        .where(KPI.id == kpi_id)
        .options(selectinload(KPI.granularities))
    )
    kpi_from_db = await session.execute(stmt)
    kpi_from_db = kpi_from_db.scalars().first()

    if kpi_from_db is None:
        raise NotFoundError(f"KPI with id = {kpi_id} does not exist!")

    return kpi_from_db


async def get_list_of_kpis(
    session: AsyncSession, requested_kpi_ids: set[int]
) -> list[KPI] | list:
    """
    This method get KPIs from DB by requested ids.
    In result, it compares requested list of ids and ids, which exists in db.
    If they are not equals: difference = non created KPIs, so we return error, in other variant requested ids
    """
    if requested_kpi_ids:
        kpi_ids = get_chunked_values_by_sqlalchemy_limit(
            some_list_with_values=requested_kpi_ids
        )

        kpis = []
        for chunk in kpi_ids:
            temp = await session.scalars(select(KPI).where(KPI.id.in_(chunk)))
            kpis.extend(temp.all())

        exists_kpi_ids = {kpi.id for kpi in kpis}
        non_exists_kpi_ids = requested_kpi_ids.difference(exists_kpi_ids)
        if non_exists_kpi_ids:
            raise NotFoundError(
                f"KPI with ids: {non_exists_kpi_ids} don't exists."
            )

        return kpis

    return []


async def create_related_kpis(
    session: AsyncSession, main_kpi: KPI, related_kpis: set[int]
) -> List[int]:
    """
    Method get Main Kpi, to which we want to add related KPIs.
    It validates related and return list of their ids
    """
    if main_kpi.id in related_kpis:
        related_kpis.remove(main_kpi.id)

    if related_kpis:
        for related_kpi in related_kpis:
            session.add(
                RelatedKPI(main_kpi=main_kpi.id, related_kpi=related_kpi)
            )
    return list(related_kpis)


async def validate_relative_kpis(
    session: AsyncSession,
    related_kpis: set[int],
    main_kpi: KPI | KPIModelCreate,
):
    await get_list_of_kpis(session=session, requested_kpi_ids=related_kpis)

    """
        This method check related KPI match with "related options".

        Related KPI has 2 options:
            - the same Object Type with main KPI
            - the same val type with main KPI
    """
    kpis = get_chunked_values_by_sqlalchemy_limit(related_kpis)
    exists_kpi = []
    for chunk in kpis:
        temp = await session.scalars(
            select(KPI).where(
                KPI.id.in_(chunk),
                KPI.label == main_kpi.label,
                KPI.object_type != main_kpi.object_type,
            )
        )
        exists_kpi.extend(temp.all())

    exists_kpi_ids = {kpi.id for kpi in exists_kpi}
    non_valid_kpi_ids = related_kpis.difference(exists_kpi_ids)
    if non_valid_kpi_ids:
        raise KPIRelatedValidationError(
            f"KPI with ids: {non_valid_kpi_ids} not valid."
            f" Related KPIs must have the same val_type and object_ids."
            f" So for this case: val_type must be {main_kpi.val_type} "
            f"and object type {main_kpi.object_type}"
        )
    return True


async def get_related_kpis_by_list_of_kpi(
    session: AsyncSession, kpi_ids: list[int]
) -> dict[int, list[int]]:
    kpi_ids = get_chunked_values_by_sqlalchemy_limit(
        some_list_with_values=kpi_ids
    )

    main_kpi_and_his_related = []
    for chunk in kpi_ids:
        stmt = select(RelatedKPI.main_kpi, RelatedKPI.related_kpi).where(
            RelatedKPI.main_kpi.in_(chunk)
        )
        main_kpi_and_his_related.extend(await session.execute(stmt))

    related_kpis_dict = defaultdict(list)
    for main_kpi, related_kpi in main_kpi_and_his_related:
        related_kpis_dict[main_kpi].append(related_kpi)

    return dict(related_kpis_dict)


async def add_related_kpis_to_main(
    session: AsyncSession, main_kpis: list[KPI]
) -> list[KPI]:
    """
    This method get related KPIs by main, and return list of related KPIs
    """
    kpi_with_related = await get_related_kpis_by_list_of_kpi(
        session=session, kpi_ids=[kpi.id for kpi in main_kpis]
    )

    for kpi in main_kpis:
        kpi.__dict__["related_kpis"] = kpi_with_related.get(kpi.id, [])
    return main_kpis


async def remove_all_related_kpis_for_kpis(
    session: AsyncSession, main_kpi_ids: List[int]
):
    await session.execute(
        delete(RelatedKPI).where(RelatedKPI.main_kpi.in_(main_kpi_ids))
    )


async def update_kpi_related_kpis(
    session: AsyncSession, main_kpi: KPI, related_kpis: set[int]
) -> List[int]:
    """
    This method updates related KPIs by main.
    It`s possible by 2 steps:
        1. Remove all links(related KPIs) from db by main KPI;
        2. Create new links.
    """
    await remove_all_related_kpis_for_kpis(
        session=session, main_kpi_ids=[main_kpi.id]
    )
    await validate_relative_kpis(
        session=session, related_kpis=related_kpis, main_kpi=main_kpi
    )
    return await create_related_kpis(
        session=session, main_kpi=main_kpi, related_kpis=related_kpis
    )


async def get_list_of_kpi_with_related(
    session: AsyncSession, kpi_ids: list[int] | set[int]
):
    kpi_ids = get_chunked_values_by_sqlalchemy_limit(kpi_ids)
    response = []
    kpis = []
    for chunk in kpi_ids:
        temp = await session.execute(
            select(KPI)
            .where(KPI.id.in_(chunk))
            .options(selectinload(KPI.related_kpis))
        )
        kpis.extend(temp.scalars().all())

    for kpi in kpis:
        temp_kpi = kpi.__dict__
        temp_kpi["related_kpis"] = (
            [related.id for related in kpi.related_kpis]
            if kpi.related_kpis
            else []
        )
        response.append(temp_kpi)

    return response


async def get_list_of_kpi_without_related(
    session: AsyncSession, kpi_ids: list[int] | set[int]
):
    kpi_ids = get_chunked_values_by_sqlalchemy_limit(kpi_ids)
    kpis = []
    for chunk in kpi_ids:
        temp = await session.execute(select(KPI).where(KPI.id.in_(chunk)))
        kpis.extend(temp.scalars().all())

    return kpis


async def get_kpi_with_related(session: AsyncSession, kpi_id: int):
    kpi = await session.execute(
        select(KPI)
        .where(KPI.id == kpi_id)
        .options(selectinload(KPI.related_kpis))
    )
    kpi = kpi.scalar()

    if kpi:
        kpi = kpi.__dict__
        kpi.pop("_sa_instance_state")
        kpi["related_kpis"] = (
            [related.id for related in kpi["related_kpis"]]
            if kpi["related_kpis"]
            else []
        )

    return kpi


async def create_links(session: AsyncSession, main_kpi: KPI):
    if main_kpi.parent_kpi:
        query = (
            update(KPI)
            .values(child_kpi=main_kpi.id)
            .where(KPI.id == main_kpi.parent_kpi)
        )
        await session.execute(query)

    if main_kpi.child_kpi:
        query = (
            update(KPI)
            .values(parent_kpi=main_kpi.id)
            .where(KPI.id == main_kpi.parent_kpi)
        )
        await session.execute(query)


async def validate_links(
    session: AsyncSession,
    main_kpi: KPIModelCreate | KPIModelPartialUpdate,
    kpi_id: int | None = None,
):
    if kpi_id and (
        kpi_id == main_kpi.parent_kpi or kpi_id == main_kpi.child_kpi
    ):
        raise KPILinkValidationError("KPI cannot link itself!")

    if main_kpi.parent_kpi:
        query = select(KPI).where(
            KPI.id == main_kpi.parent_kpi,
            KPI.object_type != main_kpi.object_type,
            KPI.child_kpi.is_(None),
        )
        parent_kpi = await session.execute(query)
        parent_kpi = parent_kpi.scalar()
        if not parent_kpi:
            raise NotFoundError(
                "Provided KPI does not exist or cannot be set as parent!"
            )

    if main_kpi.child_kpi:
        query = select(KPI).where(
            KPI.id == main_kpi.child_kpi,
            KPI.object_type != main_kpi.object_type,
            KPI.parent_kpi.is_(None),
        )
        child_kpi = await session.execute(query)
        child_kpi = child_kpi.scalar()
        if not child_kpi:
            raise NotFoundError(
                "Provided KPI does not exist or cannot be set as child!"
            )


async def update_kpi_links(
    session: AsyncSession, kpi_id: int, main_kpi: KPIModelPartialUpdate
):
    query = select(KPI).where(KPI.id == kpi_id)
    current = await session.execute(query)
    current = current.scalar()

    if main_kpi.parent_kpi:
        # remove link of current parent
        query = (
            update(KPI)
            .values(child_kpi=None)
            .where(KPI.id == current.parent_kpi)
        )
        await session.execute(query)

        query = (
            update(KPI)
            .values(child_kpi=kpi_id)
            .where(KPI.id == main_kpi.parent_kpi)
        )
        await session.execute(query)

    if main_kpi.child_kpi:
        # remove link of current child
        query = (
            update(KPI)
            .values(parent_kpi=None)
            .where(KPI.id == current.child_kpi)
        )
        await session.execute(query)

        query = (
            update(KPI)
            .values(parent_kpi=kpi_id)
            .where(KPI.id == main_kpi.child_kpi)
        )
        await session.execute(query)
