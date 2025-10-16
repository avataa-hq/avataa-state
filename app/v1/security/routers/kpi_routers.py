from fastapi import APIRouter, Depends, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession

from v1.database import database
from v1.database.schemas import KPI, KPIPermission
from v1.security.data.utils import PREFIX
from v1.security.routers.models.request_models import (
    CreatePermission,
    CreatePermissions,
    UpdatePermission,
)
from v1.security.routers.models.response_models import PermissionResponse
from v1.security.routers.utils.functions import (
    get_all_permissions,
    create_permission,
    get_permissions,
    create_permissions,
    delete_object,
    delete_objects,
    update_permission,
)
from v1.security.routers.utils.utils import transform

router = APIRouter(prefix=f"{PREFIX}/kpi", tags=["Permissions: KPIs"])

MAIN_TABLE = KPI
PERMISSION_TABLE = KPIPermission


@router.get("/", response_model=list[PermissionResponse])
async def get_all_kpi_permissions(
    session: AsyncSession = Depends(database.get_session),
):
    raw_objects = await get_all_permissions(
        session=session, permission_table=PERMISSION_TABLE
    )
    return transform(raw_objects)


@router.get("/{kpi_id}", response_model=list[PermissionResponse])
async def get_kpi_permissions(
    kpi_id: int = Path(...),
    session: AsyncSession = Depends(database.get_session),
):
    raw_objects = await get_permissions(
        session=session, permission_table=PERMISSION_TABLE, parent_id=kpi_id
    )
    return transform(raw_objects)


@router.post("/", status_code=201)
async def create_kpi_permission(
    item: CreatePermission,
    session: AsyncSession = Depends(database.get_session),
):
    return await create_permission(
        session=session,
        permission_table=PERMISSION_TABLE,
        item=item,
        main_table=MAIN_TABLE,
    )


@router.post("/multiple", status_code=201)
async def create_kpi_permissions(
    items: CreatePermissions,
    session: AsyncSession = Depends(database.get_session),
):
    return await create_permissions(
        session=session,
        permission_table=PERMISSION_TABLE,
        items=items,
        main_table=MAIN_TABLE,
    )


@router.patch("/{id}", status_code=204)
async def update_kpi_permission(
    id_: int = Path(..., alias="id"),
    item: UpdatePermission = Body(...),
    session: AsyncSession = Depends(database.get_session),
):
    return await update_permission(
        session=session,
        permission_table=PERMISSION_TABLE,
        item=item,
        item_id=id_,
        main_table=MAIN_TABLE,
    )


@router.delete("/multiple", status_code=204)
async def delete_kpi_permissions(
    id_: list[int] = Body(..., alias="ids", min_items=1),
    session: AsyncSession = Depends(database.get_session),
):
    return await delete_objects(
        session=session,
        permission_table=PERMISSION_TABLE,
        item_ids=id_,
        main_table=MAIN_TABLE,
    )


@router.delete("/{id}", status_code=204)
async def delete_kpi_permission(
    id_: int = Path(..., alias="id"),
    session: AsyncSession = Depends(database.get_session),
):
    return await delete_object(
        session=session,
        permission_table=PERMISSION_TABLE,
        item_id=id_,
        main_table=MAIN_TABLE,
    )
