from typing import Union

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from v1.security.data.utils import add_security_data
from v1.security.utils import get_admin_user_model
from v1.settings.config import DATABASE_URL
from sqlalchemy.orm import sessionmaker
from v1.database.schemas import Base
from fastapi.requests import Request

engine = create_async_engine(
    DATABASE_URL, echo=False, pool_size=20, max_overflow=100
)
session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
SQLALCHEMY_LIMIT = 32000


async def init_tables():
    """Initialize tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session(request: Request = None):
    async with session_maker() as session:
        if request:
            add_security_data(
                session=session,
                user_data=get_admin_user_model(),
                request=request,
            )
        yield session


def get_chunked_values_by_sqlalchemy_limit(
    some_list_with_values: Union[list, set, dict.keys],
) -> list[list]:
    if not some_list_with_values:
        return []

    some_list_with_values = list(some_list_with_values)
    for index in range(0, len(some_list_with_values), SQLALCHEMY_LIMIT):
        yield some_list_with_values[index : index + SQLALCHEMY_LIMIT]
