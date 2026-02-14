import io
from uuid import uuid4

import pytest
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BookNotFoundException, UnsupportedFileTypeException
from app.models.book import Book
from app.schemas.book import BookCreate, BookUpdate
from app.services.book_service import BookService
from tests.conftest import InMemoryStorage


@pytest.mark.asyncio
class TestBookServiceCreate:
    async def test_create_book_with_valid_pdf(self, db_session: AsyncSession) -> None:
        storage = InMemoryStorage()
        bg_tasks = BackgroundTasks()
        service = BookService(db_session, storage, bg_tasks)

        data = BookCreate(title="Test Book", author="Author", genre="Fiction")
        file_content = io.BytesIO(b"fake pdf content")

        result = await service.create_book(
            data=data,
            file_content=file_content,
            file_name="test.pdf",
            content_type="application/pdf",
        )

        assert result.title == "Test Book"
        assert result.author == "Author"
        assert result.genre == "Fiction"
        assert result.summary_status == "pending"
        assert result.file_type == "pdf"

    async def test_create_book_with_txt_file(self, db_session: AsyncSession) -> None:
        storage = InMemoryStorage()
        bg_tasks = BackgroundTasks()
        service = BookService(db_session, storage, bg_tasks)

        data = BookCreate(title="Text Book", author="Author", genre="Science")
        file_content = io.BytesIO(b"This is a text book content")

        result = await service.create_book(
            data=data,
            file_content=file_content,
            file_name="book.txt",
            content_type="text/plain",
        )

        assert result.file_type == "txt"
        assert result.summary_status == "pending"

    async def test_create_book_rejects_unsupported_type(
        self, db_session: AsyncSession,
    ) -> None:
        storage = InMemoryStorage()
        bg_tasks = BackgroundTasks()
        service = BookService(db_session, storage, bg_tasks)

        data = BookCreate(title="Bad Book", author="Author", genre="Fiction")
        file_content = io.BytesIO(b"fake content")

        with pytest.raises(UnsupportedFileTypeException):
            await service.create_book(
                data=data,
                file_content=file_content,
                file_name="book.exe",
                content_type="application/octet-stream",
            )


@pytest.mark.asyncio
class TestBookServiceRead:
    async def test_get_nonexistent_book_raises(self, db_session: AsyncSession) -> None:
        storage = InMemoryStorage()
        bg_tasks = BackgroundTasks()
        service = BookService(db_session, storage, bg_tasks)

        with pytest.raises(BookNotFoundException):
            await service.get_book(uuid4())

    async def test_list_books_returns_paginated(self, db_session: AsyncSession) -> None:
        storage = InMemoryStorage()
        bg_tasks = BackgroundTasks()
        service = BookService(db_session, storage, bg_tasks)

        # Create some books directly
        for i in range(3):
            book = Book(
                title=f"Book {i}",
                author="Author",
                genre="Fiction",
                file_path=f"books/{i}.pdf",
                file_type="pdf",
                summary_status="pending",
            )
            db_session.add(book)
        await db_session.flush()

        result = await service.list_books(page=1, page_size=2)
        assert result.total == 3
        assert len(result.items) == 2
        assert result.total_pages == 2


@pytest.mark.asyncio
class TestBookServiceUpdate:
    async def test_update_book_title(self, db_session: AsyncSession) -> None:
        storage = InMemoryStorage()
        bg_tasks = BackgroundTasks()
        service = BookService(db_session, storage, bg_tasks)

        book = Book(
            title="Original Title",
            author="Author",
            genre="Fiction",
            file_path="books/test.pdf",
            file_type="pdf",
            summary_status="pending",
        )
        db_session.add(book)
        await db_session.flush()
        await db_session.refresh(book)

        result = await service.update_book(book.id, BookUpdate(title="Updated Title"))
        assert result.title == "Updated Title"

    async def test_update_nonexistent_book_raises(self, db_session: AsyncSession) -> None:
        storage = InMemoryStorage()
        bg_tasks = BackgroundTasks()
        service = BookService(db_session, storage, bg_tasks)

        with pytest.raises(BookNotFoundException):
            await service.update_book(uuid4(), BookUpdate(title="New"))


@pytest.mark.asyncio
class TestBookServiceDelete:
    async def test_delete_book_removes_from_db(self, db_session: AsyncSession) -> None:
        storage = InMemoryStorage()
        await storage.upload_file(io.BytesIO(b"content"), "books/del.pdf", "application/pdf")
        bg_tasks = BackgroundTasks()
        service = BookService(db_session, storage, bg_tasks)

        book = Book(
            title="Delete Me",
            author="Author",
            genre="Fiction",
            file_path="books/del.pdf",
            file_type="pdf",
            summary_status="pending",
        )
        db_session.add(book)
        await db_session.flush()
        await db_session.refresh(book)

        await service.delete_book(book.id)

        with pytest.raises(BookNotFoundException):
            await service.get_book(book.id)
