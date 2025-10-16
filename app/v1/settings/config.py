import os

DB_TYPE = os.environ.get("V1_DB_TYPE", "postgresql+asyncpg")
DB_USER = os.environ.get("V1_DB_USER", "object_state_admin")
DB_PASS = os.environ.get("V1_DB_PASS", "root")
DB_HOST = os.environ.get("V1_DB_HOST", "localhost")
DB_PORT = os.environ.get("V1_DB_PORT", "5432")
DB_NAME = os.environ.get("V1_DB_NAME", "object_state")

DATABASE_URL = f"{DB_TYPE}://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

GRPC_PORT = os.environ.get("GRPC_PORT", "50051")

DEFAULT_ADMIN_ROLE = "__admin"

FRONTEND_SETTINGS_HOST = os.environ.get("FRONTEND_SETTINGS_HOST", "localhost")
FRONTEND_SETTINGS_GRPC_PORT = os.environ.get(
    "FRONTEND_SETTINGS_GRPC_PORT", "50051"
)
