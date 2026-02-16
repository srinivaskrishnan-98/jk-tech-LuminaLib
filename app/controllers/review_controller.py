"""Review controller handling book reviews and analysis."""
from uuid import UUID

from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.review import BookAnalysisResponse, ReviewCreate, ReviewResponse
from app.services.review_service import ReviewService


class ReviewController:
    """Controller for review submission and analysis endpoints."""

    def __init__(self, session: AsyncSession, background_tasks: BackgroundTasks) -> None:
        self.session = session
        self.background_tasks = background_tasks
        self.service = ReviewService(session, background_tasks)

    async def submit_review(
        self, user: User, book_id: UUID, data: ReviewCreate
    ) -> ReviewResponse:
        """Submit a review for a book."""
        return await self.service.submit_review(user.id, book_id, data)

    async def get_book_analysis(self, book_id: UUID) -> BookAnalysisResponse:
        """Get aggregated review analysis for a book."""
        return await self.service.get_book_analysis(book_id)
