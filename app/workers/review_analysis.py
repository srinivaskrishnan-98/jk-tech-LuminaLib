from uuid import UUID

import structlog

from app.config import Settings
from app.core.database import async_session_factory
from app.infrastructure.llm.factory import create_llm_provider
from app.repositories.book_repository import BookRepository
from app.repositories.review_repository import ReviewRepository

logger = structlog.get_logger()


async def update_review_consensus(book_id: UUID) -> None:
    """Background task: aggregate all reviews for a book and generate a consensus summary.

    Fetches all reviews, sends them to the LLM for sentiment analysis,
    and updates the book's review_consensus field.
    """
    settings = Settings()
    llm = create_llm_provider(settings)

    async with async_session_factory() as session:
        try:
            review_repo = ReviewRepository(session)
            book_repo = BookRepository(session)

            reviews = await review_repo.get_all_for_book(book_id)
            if not reviews:
                logger.info("no_reviews_for_consensus", book_id=str(book_id))
                return

            logger.info(
                "consensus_generation_started",
                book_id=str(book_id),
                review_count=len(reviews),
            )

            # Build review texts with ratings
            review_texts = [
                f"Rating: {r.rating}/5 - {r.review_text}" for r in reviews
            ]

            # Analyze sentiment for each review
            for review in reviews:
                if review.sentiment_score is None:
                    sentiment = await llm.analyze_sentiment(review.review_text)
                    review.sentiment_score = sentiment.get("score", 0.5)

            # Generate consensus summary
            consensus = await llm.generate_review_consensus(review_texts)

            # Update book record
            book = await book_repo.get_by_id(book_id)
            if book:
                book.review_consensus = consensus

            await session.commit()
            logger.info("consensus_generation_completed", book_id=str(book_id))

        except Exception:
            logger.exception("consensus_generation_failed", book_id=str(book_id))
