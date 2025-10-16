"""Async gRPC server"""

import asyncio
import logging
import grpc

from grpc_settings.protobuf_storage.airflow_manager.protobuf_files import (
    airflow_to_state_pb2_grpc,
)
from grpc_settings.protobuf_storage.airflow_manager.servicer import (
    AirflowManager,
)
from v1.settings.config import GRPC_PORT


async def start_grpc_server() -> None:
    server = grpc.aio.server()
    # airflow_manager_pb2_grpc.add_AirflowManagerServicer_to_server(AirflowManager(), server)
    airflow_to_state_pb2_grpc.add_AirflowToStateManagerServicer_to_server(
        AirflowManager(), server
    )
    listen_addr = f"[::]:{GRPC_PORT}"
    server.add_insecure_port(listen_addr)
    logging.info("Starting server on %s", listen_addr)
    await server.start()
    await server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(start_grpc_server())
