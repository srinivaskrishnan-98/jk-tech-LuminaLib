from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review import Review
from app.repositories.base import BaseRepository


class ReviewRepository(BaseRepository[Review]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Review, session)

    async def get_by_user_and_book(self, user_id: UUID, book_id: UUID) -> Review | None:
        """Check if user already reviewed this book."""
        stmt = select(Review).where(
            and_(Review.user_id == user_id, Review.book_id == book_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_for_book(self, book_id: UUID) -> list[Review]:
        """Get all reviews for a specific book."""
        stmt = (
            select(Review)
            .where(Review.book_id == book_id)
            .order_by(Review.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_all_for_user(self, user_id: UUID) -> list[Review]:
        """Get all reviews by a specific user."""
        stmt = select(Review).where(Review.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_average_rating(self, book_id: UUID) -> float | None:
        """Get average rating for a book."""
        stmt = select(func.avg(Review.rating)).where(Review.book_id == book_id)
        result = await self.session.execute(stmt)
        avg = result.scalar_one_or_none()
        return round(float(avg), 2) if avg is not None else None

    async def get_rating_distribution(self, book_id: UUID) -> dict[str, int]:
        """Get count of reviews per rating level."""
        stmt = (
            select(Review.rating, func.count(Review.id))
            .where(Review.book_id == book_id)
            .group_by(Review.rating)
        )
        result = await self.session.execute(stmt)
        distribution = {str(i): 0 for i in range(1, 6)}
        for rating, count in result.all():
            distribution[str(rating)] = count
        return distribution

    async def count_for_book(self, book_id: UUID) -> int:
        """Count total reviews for a book."""
        stmt = select(func.count()).select_from(Review).where(Review.book_id == book_id)
        result = await self.session.execute(stmt)
        return result.scalar_one()
