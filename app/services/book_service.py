import math
import uuid
from typing import BinaryIO

import structlog
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BookNotFoundException,
    UnsupportedFileTypeException,
)
from app.interfaces.storage import StorageBackend
from app.models.book import Book
from app.repositories.book_repository import BookRepository
from app.schemas.book import BookCreate, BookResponse, BookUpdate
from app.schemas.common import PaginatedResponse
from app.workers.summarization import summarize_book

logger = structlog.get_logger()

ALLOWED_FILE_TYPES = {"pdf", "txt"}


class BookService:
    """Handles book CRUD operations and file upload orchestration."""

    def __init__(
        self,
        session: AsyncSession,
        storage: StorageBackend,
        background_tasks: BackgroundTasks,
    ) -> None:
        self.session = session
        self.storage = storage
        self.background_tasks = background_tasks
        self.repo = BookRepository(session)

    async def create_book(
        self,
        data: BookCreate,
        file_content: BinaryIO,
        file_name: str,
        content_type: str,
    ) -> BookResponse:
        """Upload a book file and create metadata. Triggers async summarization."""
        # Validate file type
        file_ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
        if file_ext not in ALLOWED_FILE_TYPES:
            raise UnsupportedFileTypeException(file_ext)

        logger.info("creating_book", title=data.title, file_type=file_ext)

        # Upload file to storage
        file_key = f"books/{uuid.uuid4()}/{file_name}"
        await self.storage.upload_file(file_content, file_key, content_type)

        # Create book record
        book = Book(
            title=data.title,
            author=data.author,
            isbn=data.isbn,
            genre=data.genre,
            description=data.description,
            file_path=file_key,
            file_type=file_ext,
            summary_status="pending",
            total_copies=data.total_copies,
            available_copies=data.total_copies,
        )
        book = await self.repo.create(book)

        # Trigger async summarization
        self.background_tasks.add_task(summarize_book, book.id)

        logger.info("book_created", book_id=str(book.id), summary_status="pending")
        return BookResponse.model_validate(book)

    async def get_book(self, book_id: uuid.UUID) -> BookResponse:
        """Get a single book by ID."""
        book = await self.repo.get_by_id(book_id)
        if not book:
            raise BookNotFoundException(book_id)
        return BookResponse.model_validate(book)

    async def list_books(
        self, *, page: int = 1, page_size: int = 20
    ) -> PaginatedResponse[BookResponse]:
        """List books with pagination."""
        offset = (page - 1) * page_size
        books, total = await self.repo.get_paginated(skip=offset, limit=page_size)
        total_pages = math.ceil(total / page_size) if total > 0 else 0

        return PaginatedResponse(
            items=[BookResponse.model_validate(b) for b in books],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def update_book(
        self, book_id: uuid.UUID, data: BookUpdate
    ) -> BookResponse:
        """Update book metadata."""
        book = await self.repo.get_by_id(book_id)
        if not book:
            raise BookNotFoundException(book_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(book, field, value)

        # Adjust available copies if total_copies changed
        if "total_copies" in update_data:
            borrowed = book.total_copies - book.available_copies
            book.available_copies = max(0, data.total_copies - borrowed)  # type: ignore[operator]

        book = await self.repo.update(book)
        logger.info("book_updated", book_id=str(book_id))
        return BookResponse.model_validate(book)

    async def delete_book(self, book_id: uuid.UUID) -> None:
        """Delete a book and its associated file from storage."""
        book = await self.repo.get_by_id(book_id)
        if not book:
            raise BookNotFoundException(book_id)

        # Delete file from storage
        try:
            await self.storage.delete_file(book.file_path)
        except Exception:
            logger.warning("file_deletion_failed", book_id=str(book_id), file_path=book.file_path)

        await self.repo.delete(book)
        logger.info("book_deleted", book_id=str(book_id))
