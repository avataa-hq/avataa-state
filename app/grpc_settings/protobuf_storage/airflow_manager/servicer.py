import datetime
from typing import AsyncIterator

import grpc
from sqlalchemy import select

from grpc_settings.protobuf_storage.airflow_manager.protobuf_files.airflow_to_state_pb2 import (
    RequestBatchImport,
    ResponseBatchImport,
)
from grpc_settings.protobuf_storage.airflow_manager.protobuf_files.airflow_to_state_pb2_grpc import (
    AirflowToStateManagerServicer,
)
from v1.database.database import get_session
from v1.database.schemas import KPI, KPIValue
from v1.utils.val_type_validators import get_value_validate_funct_for_kpi


class AirflowManager(AirflowToStateManagerServicer):
    async def BatchImport(
        self,
        request_iterator: AsyncIterator[RequestBatchImport],
        context: grpc.ServicerContext,
    ) -> ResponseBatchImport:
        # MAIN PROCESS
        async for session in get_session():
            async for req in request_iterator:
                # firstly we get all requested kpi, to check if kpi already exists
                # because if kpi is not exists it`s useless to validate future data
                # we store them in list, not in set, because it future we will use them
                # and if we store them in set we will lose sequence
                requested_kpi_ids = set()
                for kpi_item in req.kpi_data:
                    requested_kpi_ids.add(kpi_item.kpi_id)

                # get existed kpi_ids
                stmt = select(KPI.id).where(KPI.id.in_(requested_kpi_ids))
                exists_kpi_ids = await session.execute(stmt)
                exists_kpi_ids = exists_kpi_ids.scalars().all()

                # get difference between exists kpis and requested
                kpi_which_not_exist = requested_kpi_ids.difference(
                    set(exists_kpi_ids)
                )
                if kpi_which_not_exist:
                    return ResponseBatchImport(
                        status="ERROR",
                        message=f"There are kpis, which "
                        f"don't exist: {kpi_which_not_exist}",
                    )
                # after we make main validation -- kpi_id existing check
                # we need to validate status firstly, because if status wrong -- we can't validate value by val_type
                # which is harder operation

                # but as base for value validation -- we need to collect info about him: val_type and multiple attrs.
                stmt = select(KPI.id, KPI.val_type, KPI.multiple).where(
                    KPI.id.in_(requested_kpi_ids)
                )
                response = await session.execute(stmt)
                response = response.fetchall()

                # structure like {1: [str, True]}
                kpis_and_val_types = {
                    res[0]: [res[1], res[2]] for res in response
                }

                for kpi_item in req.kpi_data:
                    # value validation by val_type and multiple attrs
                    try:
                        val_type_validation_func = (
                            get_value_validate_funct_for_kpi(
                                kpi_val_type=kpis_and_val_types.get(
                                    kpi_item.kpi_id
                                )[0],
                                kpi_multiple=kpis_and_val_types.get(
                                    kpi_item.kpi_id
                                )[1],
                            )
                        )
                        val_type_validation_func(kpi_item.value)
                    except ValueError as message_error:
                        message_error = str(message_error)
                        return ResponseBatchImport(
                            status="ERROR",
                            message=message_error
                            + f"For kpi_id = {kpi_item.kpi_id}.",
                        )

                    states = {0: "current", 1: "historical", 2: "planned"}
                    kpi = KPIValue(
                        kpi_id=kpi_item.kpi_id,
                        granularity_id=kpi_item.granularity_id,
                        object_id=kpi_item.object_id,
                        value=kpi_item.value,
                        record_time=datetime.datetime.fromtimestamp(
                            kpi_item.record_time.seconds
                        ),
                        state=states[kpi_item.state],
                    )
                    session.add(kpi)
                await session.flush()
            await session.commit()
        return ResponseBatchImport(status="OK")
