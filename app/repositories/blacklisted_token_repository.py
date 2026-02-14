from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.blacklisted_token import BlacklistedToken
from app.repositories.base import BaseRepository


class BlacklistedTokenRepository(BaseRepository[BlacklistedToken]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(BlacklistedToken, session)

    async def get_by_jti(self, jti: str) -> BlacklistedToken | None:
        stmt = select(BlacklistedToken).where(BlacklistedToken.token_jti == jti)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def is_blacklisted(self, jti: str) -> bool:
        return await self.get_by_jti(jti) is not None
