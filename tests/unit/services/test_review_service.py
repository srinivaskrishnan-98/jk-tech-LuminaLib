from uuid import uuid4

import pytest
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AlreadyReviewedException,
    BookNotFoundException,
    MustBorrowBeforeReviewException,
)
from app.models.book import Book
from app.models.borrow import Borrow
from app.schemas.review import ReviewCreate
from app.services.review_service import ReviewService


@pytest.mark.asyncio
class TestReviewService:
    async def _create_book(self, db_session: AsyncSession) -> Book:
        book = Book(
            title="Reviewable Book",
            author="Author",
            genre="Fiction",
            file_path="books/review.pdf",
            file_type="pdf",
            summary_status="completed",
        )
        db_session.add(book)
        await db_session.flush()
        await db_session.refresh(book)
        return book

    async def _create_borrow(self, db_session: AsyncSession, user_id, book_id) -> Borrow:
        borrow = Borrow(user_id=user_id, book_id=book_id)
        db_session.add(borrow)
        await db_session.flush()
        return borrow

    async def test_submit_review_after_borrowing(self, db_session: AsyncSession, test_user) -> None:
        book = await self._create_book(db_session)
        await self._create_borrow(db_session, test_user.id, book.id)

        service = ReviewService(db_session, BackgroundTasks())
        data = ReviewCreate(rating=5, review_text="This is an excellent book that I really enjoyed!")

        result = await service.submit_review(test_user.id, book.id, data)
        assert result.rating == 5
        assert result.book_id == book.id
        assert result.user_id == test_user.id

    async def test_review_without_borrowing_raises(self, db_session: AsyncSession, test_user) -> None:
        book = await self._create_book(db_session)

        service = ReviewService(db_session, BackgroundTasks())
        data = ReviewCreate(rating=4, review_text="This is a great book that I enjoyed!")

        with pytest.raises(MustBorrowBeforeReviewException):
            await service.submit_review(test_user.id, book.id, data)

    async def test_duplicate_review_raises(self, db_session: AsyncSession, test_user) -> None:
        book = await self._create_book(db_session)
        await self._create_borrow(db_session, test_user.id, book.id)

        service = ReviewService(db_session, BackgroundTasks())
        data = ReviewCreate(rating=5, review_text="First review of this wonderful book!")

        await service.submit_review(test_user.id, book.id, data)
        with pytest.raises(AlreadyReviewedException):
            await service.submit_review(test_user.id, book.id, data)

    async def test_review_nonexistent_book_raises(self, db_session: AsyncSession, test_user) -> None:
        service = ReviewService(db_session, BackgroundTasks())
        data = ReviewCreate(rating=3, review_text="This book was okay I suppose.")

        with pytest.raises(BookNotFoundException):
            await service.submit_review(test_user.id, uuid4(), data)

    async def test_get_book_analysis(self, db_session: AsyncSession, test_user) -> None:
        book = await self._create_book(db_session)

        service = ReviewService(db_session, BackgroundTasks())
        result = await service.get_book_analysis(book.id)

        assert result.book_id == book.id
        assert result.total_reviews == 0
        assert result.average_rating is None
