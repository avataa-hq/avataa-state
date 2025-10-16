import json
from typing import List

import grpc
from fastapi import APIRouter, Depends
from grpc.aio import AioRpcError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from grpc_settings.protobuf_storage.frontend_settings_proto import (
    frontend_settings_pb2_grpc,
    frontend_settings_pb2,
)

from v1.database.database import get_session, SQLALCHEMY_LIMIT
from v1.database.schemas import KPI
from v1.models.kpi import SetCustomPalette
from v1.routers.palette.utils import create_default_palette_for_kpis
from v1.settings.config import (
    FRONTEND_SETTINGS_HOST,
    FRONTEND_SETTINGS_GRPC_PORT,
)

router = APIRouter(prefix="/palette", tags=["Palette"])


@router.post("/set_default_palette", status_code=200)
async def set_default_palette(session: AsyncSession = Depends(get_session)):
    """
    This endpoint set palette for KPIs, which doesn't have palette
    """
    exists_kpis = []

    stream = await session.stream(
        select(KPI).execution_options(yield_per=SQLALCHEMY_LIMIT)
    )
    async for kpi in stream:
        exists_kpis.extend(kpi)

    wrong_kpi_ids = await create_default_palette_for_kpis(kpis=exists_kpis)
    return wrong_kpi_ids


@router.post("/set_custom_palette", status_code=200)
async def set_custom_palette(kpi_with_palette: List[SetCustomPalette]):
    kpis_with_palettes = []

    async with grpc.aio.insecure_channel(
        f"{FRONTEND_SETTINGS_HOST}:{FRONTEND_SETTINGS_GRPC_PORT}"
    ) as channel:
        try:
            stub = frontend_settings_pb2_grpc.FrontendSettingsStub(channel)

            for kpi in kpi_with_palette:
                preference_instance = (
                    frontend_settings_pb2.PreferenceInstanceForWithPalette(
                        preference_name=kpi.kpi_name,
                        val_type=kpi.val_type,
                        kpi_id=kpi.kpi_id,
                        palette=json.dumps(kpi.palette),
                        object_type_id=kpi.object_type_id,
                    )
                )

                kpis_with_palettes.append(preference_instance)

            request = frontend_settings_pb2.RequestToSetCustomPalette(
                preference_instances=kpis_with_palettes
            )
            response = await stub.SetCustomColorRangeForKPI(request)
            return response.wrong_kpi_ids

        except AioRpcError as e:
            print(f"ERROR {e}")
