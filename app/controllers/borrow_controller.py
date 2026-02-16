"""Borrow controller handling book borrowing and returns."""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.borrow import BorrowResponse
from app.services.borrow_service import BorrowService


class BorrowController:
    """Controller for book borrowing and return endpoints."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.service = BorrowService(session)

    async def borrow_book(self, user: User, book_id: UUID) -> BorrowResponse:
        """Borrow a book from the library."""
        return await self.service.borrow_book(user.id, book_id)

    async def return_book(self, user: User, book_id: UUID) -> BorrowResponse:
        """Return a borrowed book to the library."""
        return await self.service.return_book(user.id, book_id)
