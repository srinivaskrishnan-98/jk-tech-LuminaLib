from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AlreadyBorrowedError,
    BookNotAvailableError,
    BookNotFoundError,
    NoBorrowFoundError,
)
from app.models.borrow import Borrow
from app.repositories.book_repository import BookRepository
from app.repositories.borrow_repository import BorrowRepository
from app.schemas.borrow import BorrowResponse
from app.services.recommendation_service import RecommendationService

logger = structlog.get_logger()


class BorrowService:
    """Handles book borrow and return business logic."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.borrow_repo = BorrowRepository(session)
        self.book_repo = BookRepository(session)

    async def borrow_book(self, user_id: UUID, book_id: UUID) -> BorrowResponse:
        """Borrow a book. Decrements available copies atomically."""
        # Use SELECT FOR UPDATE to prevent race conditions
        book = await self.book_repo.get_for_update(book_id)
        if not book:
            raise BookNotFoundError(book_id)

        if book.available_copies <= 0:
            raise BookNotAvailableError(book_id)

        # Check for existing active borrow
        existing = await self.borrow_repo.get_active_borrow(user_id, book_id)
        if existing:
            raise AlreadyBorrowedError(book_id)

        # Decrement available copies
        book.available_copies -= 1

        # Create borrow record
        borrow = Borrow(user_id=user_id, book_id=book_id)
        borrow = await self.borrow_repo.create(borrow)

        # Update implicit preferences
        rec_service = RecommendationService(self.session)
        await rec_service.update_implicit_preferences(user_id)

        logger.info(
            "book_borrowed",
            user_id=str(user_id),
            book_id=str(book_id),
            remaining_copies=book.available_copies,
        )
        return BorrowResponse.model_validate(borrow)

    async def return_book(self, user_id: UUID, book_id: UUID) -> BorrowResponse:
        """Return a borrowed book. Increments available copies."""
        borrow = await self.borrow_repo.get_active_borrow(user_id, book_id)
        if not borrow:
            raise NoBorrowFoundError(book_id)

        borrow.returned_at = datetime.now(UTC)
        borrow.is_active = False
        await self.borrow_repo.update(borrow)

        book = await self.book_repo.get_for_update(book_id)
        if book:
            book.available_copies += 1
            await self.session.flush()

        logger.info(
            "book_returned",
            user_id=str(user_id),
            book_id=str(book_id),
        )
        return BorrowResponse.model_validate(borrow)
