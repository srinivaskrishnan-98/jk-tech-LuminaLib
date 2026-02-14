from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Form, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_storage_backend
from app.interfaces.storage import StorageBackend
from app.models.user import User
from app.schemas.book import BookCreate, BookResponse, BookUpdate
from app.schemas.borrow import BorrowResponse
from app.schemas.common import MessageResponse, PaginatedResponse
from app.services.book_service import BookService
from app.services.borrow_service import BorrowService

router = APIRouter()


@router.post("", response_model=BookResponse, status_code=201)
async def create_book(
    file: UploadFile,
    title: str = Form(..., max_length=500),
    author: str = Form(..., max_length=255),
    genre: str = Form(..., max_length=100),
    isbn: str | None = Form(default=None, max_length=20),
    description: str | None = Form(default=None),
    total_copies: int = Form(default=1, ge=1),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    storage: StorageBackend = Depends(get_storage_backend),
) -> BookResponse:
    """Upload a book file (PDF/TXT) with metadata. Triggers async summarization."""
    service = BookService(session, storage, background_tasks)
    data = BookCreate(
        title=title,
        author=author,
        isbn=isbn,
        genre=genre,
        description=description,
        total_copies=total_copies,
    )
    return await service.create_book(
        data=data,
        file_content=file.file,
        file_name=file.filename or "unknown",
        content_type=file.content_type or "application/octet-stream",
    )


@router.get("", response_model=PaginatedResponse[BookResponse])
async def list_books(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    storage: StorageBackend = Depends(get_storage_backend),
) -> PaginatedResponse[BookResponse]:
    """List all books with pagination."""
    service = BookService(session, storage, background_tasks)
    return await service.list_books(page=page, page_size=page_size)


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: UUID,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    storage: StorageBackend = Depends(get_storage_backend),
) -> BookResponse:
    """Get a single book by ID."""
    service = BookService(session, storage, background_tasks)
    return await service.get_book(book_id)


@router.put("/{book_id}", response_model=BookResponse)
async def update_book(
    book_id: UUID,
    data: BookUpdate,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    storage: StorageBackend = Depends(get_storage_backend),
) -> BookResponse:
    """Update book metadata."""
    service = BookService(session, storage, background_tasks)
    return await service.update_book(book_id, data)


@router.delete("/{book_id}", response_model=MessageResponse)
async def delete_book(
    book_id: UUID,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    storage: StorageBackend = Depends(get_storage_backend),
) -> MessageResponse:
    """Delete a book and its associated file."""
    service = BookService(session, storage, background_tasks)
    await service.delete_book(book_id)
    return MessageResponse(message="Book deleted successfully")


@router.post("/{book_id}/borrow", response_model=BorrowResponse, status_code=201)
async def borrow_book(
    book_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> BorrowResponse:
    """Borrow a book. User must not already have an active borrow for this book."""
    service = BorrowService(session)
    return await service.borrow_book(current_user.id, book_id)


@router.post("/{book_id}/return", response_model=BorrowResponse)
async def return_book(
    book_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> BorrowResponse:
    """Return a borrowed book."""
    service = BorrowService(session)
    return await service.return_book(current_user.id, book_id)
