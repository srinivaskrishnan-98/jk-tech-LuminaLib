from uuid import UUID

import structlog
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AlreadyReviewedError,
    BookNotFoundError,
    MustBorrowBeforeReviewError,
)
from app.models.review import Review
from app.repositories.book_repository import BookRepository
from app.repositories.borrow_repository import BorrowRepository
from app.repositories.review_repository import ReviewRepository
from app.schemas.review import BookAnalysisResponse, ReviewCreate, ReviewResponse
from app.workers.review_analysis import update_review_consensus

logger = structlog.get_logger()


class ReviewService:
    """Handles review submission and analysis retrieval."""

    def __init__(
        self,
        session: AsyncSession,
        background_tasks: BackgroundTasks,
    ) -> None:
        self.session = session
        self.background_tasks = background_tasks
        self.review_repo = ReviewRepository(session)
        self.borrow_repo = BorrowRepository(session)
        self.book_repo = BookRepository(session)

    async def submit_review(
        self, user_id: UUID, book_id: UUID, data: ReviewCreate
    ) -> ReviewResponse:
        """Submit a review for a book. Only users who have borrowed the book can review."""
        # Verify book exists
        book = await self.book_repo.get_by_id(book_id)
        if not book:
            raise BookNotFoundError(book_id)

        # Enforce: must have borrowed the book
        has_borrowed = await self.borrow_repo.has_ever_borrowed(user_id, book_id)
        if not has_borrowed:
            raise MustBorrowBeforeReviewError()

        # Enforce: one review per user per book
        existing = await self.review_repo.get_by_user_and_book(user_id, book_id)
        if existing:
            raise AlreadyReviewedError()

        # Create review
        review = Review(
            user_id=user_id,
            book_id=book_id,
            rating=data.rating,
            review_text=data.review_text,
        )
        review = await self.review_repo.create(review)

        # Commit to ensure review is available for background task
        await self.session.commit()

        # Trigger async consensus update
        self.background_tasks.add_task(update_review_consensus, book_id)

        logger.info(
            "review_submitted",
            user_id=str(user_id),
            book_id=str(book_id),
            rating=data.rating,
        )
        return ReviewResponse.model_validate(review)

    async def get_book_analysis(self, book_id: UUID) -> BookAnalysisResponse:
        """Get GenAI-aggregated review analysis for a book."""
        book = await self.book_repo.get_by_id(book_id)
        if not book:
            raise BookNotFoundError(book_id)

        total_reviews = await self.review_repo.count_for_book(book_id)
        avg_rating = await self.review_repo.get_average_rating(book_id)
        distribution = await self.review_repo.get_rating_distribution(book_id)

        return BookAnalysisResponse(
            book_id=book.id,
            title=book.title,
            review_consensus=book.review_consensus,
            total_reviews=total_reviews,
            average_rating=avg_rating,
            rating_distribution=distribution,
        )
