from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.book import Book
from app.repositories.base import BaseRepository


class BookRepository(BaseRepository[Book]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Book, session)

    async def get_paginated(
        self, *, skip: int = 0, limit: int = 20
    ) -> tuple[list[Book], int]:
        """Get paginated books with total count."""
        count_stmt = select(func.count()).select_from(Book)
        total = (await self.session.execute(count_stmt)).scalar_one()

        stmt = select(Book).offset(skip).limit(limit).order_by(Book.created_at.desc())
        result = await self.session.execute(stmt)
        books = list(result.scalars().all())

        return books, total

    async def get_by_isbn(self, isbn: str) -> Book | None:
        stmt = select(Book).where(Book.isbn == isbn)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_for_update(self, book_id: UUID) -> Book | None:
        """Get a book with SELECT FOR UPDATE to prevent race conditions."""
        stmt = select(Book).where(Book.id == book_id).with_for_update()
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_books(self) -> list[Book]:
        """Get all books (used by recommendation engine)."""
        stmt = select(Book).order_by(Book.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_highly_rated(self, limit: int = 10) -> list[Book]:
        """Get books with the most reviews as a cold-start fallback."""
        from app.models.review import Review

        stmt = (
            select(Book)
            .outerjoin(Review)
            .group_by(Book.id)
            .order_by(func.avg(Review.rating).desc().nullslast(), func.count(Review.id).desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
