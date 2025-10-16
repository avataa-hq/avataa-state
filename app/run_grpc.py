import logging
import asyncio
from grpc_settings.grpc_server.grpc_method_processer import start_grpc_server

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(start_grpc_server())
