"""Book controller handling book CRUD operations."""
from uuid import UUID

from fastapi import BackgroundTasks, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.infrastructure.llm.factory import create_llm_provider
from app.infrastructure.storage.factory import create_storage_backend
from app.models.user import User
from app.schemas.book import BookCreate, BookResponse, BookUpdate
from app.schemas.common import MessageResponse, PaginatedResponse
from app.services.book_service import BookService


class BookController:
    """Controller for book management endpoints."""

    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        background_tasks: BackgroundTasks,
    ) -> None:
        self.session = session
        self.settings = settings
        self.background_tasks = background_tasks
        self.service = BookService(
            session=session,
            storage=create_storage_backend(settings),
            background_tasks=background_tasks,
        )
        self.llm_provider = create_llm_provider(settings)

    async def upload_book(
        self, file: UploadFile, data: BookCreate, user: User
    ) -> BookResponse:
        """Upload a new book to the library."""
        return await self.service.create_book(
            data=data,
            file_content=file.file,
            file_name=file.filename or "unknown",
            content_type=file.content_type or "application/octet-stream",
        )

    async def list_books(self, skip: int, limit: int) -> PaginatedResponse[BookResponse]:
        """List all books with pagination."""
        # Convert skip/limit to page/page_size
        page = (skip // limit) + 1 if limit > 0 else 1
        return await self.service.list_books(page=page, page_size=limit)

    async def get_book(self, book_id: UUID) -> BookResponse:
        """Get a specific book by ID."""
        return await self.service.get_book(book_id)

    async def update_book(self, book_id: UUID, data: BookUpdate) -> BookResponse:
        """Update book metadata."""
        return await self.service.update_book(book_id, data)

    async def delete_book(self, book_id: UUID) -> MessageResponse:
        """Delete a book from the library."""
        await self.service.delete_book(book_id)
        return MessageResponse(message="Book deleted successfully")
