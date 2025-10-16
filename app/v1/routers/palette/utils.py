from collections import defaultdict
from typing import List

import grpc
from grpc.aio import AioRpcError

from grpc_settings.protobuf_storage.frontend_settings_proto import (
    frontend_settings_pb2_grpc,
    frontend_settings_pb2,
)
from v1.database.schemas import KPI
from v1.settings.config import (
    FRONTEND_SETTINGS_HOST,
    FRONTEND_SETTINGS_GRPC_PORT,
)


async def create_default_palette_for_kpis(kpis: List[KPI]):
    collected_data_for_grpc = defaultdict(list)

    async with grpc.aio.insecure_channel(
        f"{FRONTEND_SETTINGS_HOST}:{FRONTEND_SETTINGS_GRPC_PORT}"
    ) as channel:
        try:
            stub = frontend_settings_pb2_grpc.FrontendSettingsStub(channel)

            for kpi in kpis:
                preference_instance = frontend_settings_pb2.PreferenceInstance(
                    preference_name=kpi.name,
                    val_type=kpi.val_type,
                    kpi_id=kpi.id,
                )

                collected_data_for_grpc[int(kpi.object_type)].append(
                    preference_instance
                )

            # CONVERT DATA FOR GRPC
            collected_data_for_grpc = dict(collected_data_for_grpc)
            for tpo_id, preference_instances in collected_data_for_grpc.items():
                collected_data_for_grpc[tpo_id] = (
                    frontend_settings_pb2.PreferenceInstances(
                        preference_instances=preference_instances
                    )
                )

            request = frontend_settings_pb2.RequestObjectForPalette(
                tmo_id_preference=collected_data_for_grpc
            )
            response = await stub.SetDefaultPaletteForItems(request)
            return response.wrong_kpi_ids

        except AioRpcError as e:
            print(f"ERROR {e}")
