from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from v1.database.schemas import Granularity


async def get_granularity_by_id_or_raise_error(
    granularity_id: int, session: AsyncSession
):
    """Returns granularity instance, otherwise raises error."""

    stmt = select(Granularity).where(Granularity.id == granularity_id)
    res = await session.execute(stmt)
    res = res.scalars().first()

    if res is None:
        raise HTTPException(status_code=404, detail="Granularity not founded.")

    return res
