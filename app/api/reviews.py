from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.review_controller import ReviewController
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.review import BookAnalysisResponse, ReviewCreate, ReviewResponse

router = APIRouter()


@router.post("/{book_id}/reviews", response_model=ReviewResponse, status_code=201)
async def submit_review(
    book_id: UUID,
    data: ReviewCreate,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ReviewResponse:
    """Submit a review for a book. User must have borrowed the book first."""
    controller = ReviewController(session, background_tasks)
    return await controller.submit_review(current_user, book_id, data)


@router.get("/{book_id}/analysis", response_model=BookAnalysisResponse)
async def get_book_analysis(
    book_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> BookAnalysisResponse:
    """Get GenAI-aggregated summary of all reviews for a book."""
    controller = ReviewController(session, BackgroundTasks())
    return await controller.get_book_analysis(book_id)
