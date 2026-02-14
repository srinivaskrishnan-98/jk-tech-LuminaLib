from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AlreadyBorrowedException,
    BookNotAvailableException,
    BookNotFoundException,
    NoBorrowFoundException,
)
from app.models.book import Book
from app.services.borrow_service import BorrowService


@pytest.mark.asyncio
class TestBorrowService:
    async def _create_book(self, db_session: AsyncSession, copies: int = 1) -> Book:
        book = Book(
            title="Borrowable Book",
            author="Author",
            genre="Fiction",
            file_path="books/test.pdf",
            file_type="pdf",
            summary_status="completed",
            total_copies=copies,
            available_copies=copies,
        )
        db_session.add(book)
        await db_session.flush()
        await db_session.refresh(book)
        return book

    async def test_borrow_book_success(self, db_session: AsyncSession, test_user) -> None:
        book = await self._create_book(db_session)
        service = BorrowService(db_session)

        result = await service.borrow_book(test_user.id, book.id)

        assert result.user_id == test_user.id
        assert result.book_id == book.id
        assert result.is_active is True
        assert result.returned_at is None

    async def test_borrow_decrements_available_copies(self, db_session: AsyncSession, test_user) -> None:
        book = await self._create_book(db_session, copies=3)
        service = BorrowService(db_session)

        await service.borrow_book(test_user.id, book.id)
        await db_session.refresh(book)
        assert book.available_copies == 2

    async def test_borrow_nonexistent_book_raises(self, db_session: AsyncSession, test_user) -> None:
        service = BorrowService(db_session)
        with pytest.raises(BookNotFoundException):
            await service.borrow_book(test_user.id, uuid4())

    async def test_borrow_unavailable_book_raises(self, db_session: AsyncSession, test_user) -> None:
        book = await self._create_book(db_session, copies=0)
        book.available_copies = 0
        await db_session.flush()

        service = BorrowService(db_session)
        with pytest.raises(BookNotAvailableException):
            await service.borrow_book(test_user.id, book.id)

    async def test_double_borrow_raises(self, db_session: AsyncSession, test_user) -> None:
        book = await self._create_book(db_session, copies=5)
        service = BorrowService(db_session)

        await service.borrow_book(test_user.id, book.id)
        with pytest.raises(AlreadyBorrowedException):
            await service.borrow_book(test_user.id, book.id)

    async def test_return_book_success(self, db_session: AsyncSession, test_user) -> None:
        book = await self._create_book(db_session)
        service = BorrowService(db_session)

        await service.borrow_book(test_user.id, book.id)
        result = await service.return_book(test_user.id, book.id)

        assert result.is_active is False
        assert result.returned_at is not None

    async def test_return_increments_available_copies(self, db_session: AsyncSession, test_user) -> None:
        book = await self._create_book(db_session)
        service = BorrowService(db_session)

        await service.borrow_book(test_user.id, book.id)
        await db_session.refresh(book)
        assert book.available_copies == 0

        await service.return_book(test_user.id, book.id)
        await db_session.refresh(book)
        assert book.available_copies == 1

    async def test_return_without_borrow_raises(self, db_session: AsyncSession, test_user) -> None:
        book = await self._create_book(db_session)
        service = BorrowService(db_session)

        with pytest.raises(NoBorrowFoundException):
            await service.return_book(test_user.id, book.id)
