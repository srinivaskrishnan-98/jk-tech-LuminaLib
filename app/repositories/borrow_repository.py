from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.borrow import Borrow
from app.repositories.base import BaseRepository


class BorrowRepository(BaseRepository[Borrow]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Borrow, session)

    async def get_active_borrow(self, user_id: UUID, book_id: UUID) -> Borrow | None:
        """Get active (unreturned) borrow for a specific user and book."""
        stmt = select(Borrow).where(
            and_(
                Borrow.user_id == user_id,
                Borrow.book_id == book_id,
                Borrow.is_active.is_(True),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def has_ever_borrowed(self, user_id: UUID, book_id: UUID) -> bool:
        """Check if a user has ever borrowed a specific book (active or returned)."""
        stmt = select(Borrow).where(
            and_(
                Borrow.user_id == user_id,
                Borrow.book_id == book_id,
            )
        ).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_all_for_user(self, user_id: UUID) -> list[Borrow]:
        """Get all borrows (active and returned) for a user."""
        stmt = (
            select(Borrow)
            .where(Borrow.user_id == user_id)
            .order_by(Borrow.borrowed_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_for_user(self, user_id: UUID) -> list[Borrow]:
        """Get all currently active borrows for a user."""
        stmt = select(Borrow).where(
            and_(Borrow.user_id == user_id, Borrow.is_active.is_(True))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
