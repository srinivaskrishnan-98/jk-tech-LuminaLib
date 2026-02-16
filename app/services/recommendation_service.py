from uuid import UUID

import numpy as np
import structlog
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.book_repository import BookRepository
from app.repositories.borrow_repository import BorrowRepository
from app.repositories.review_repository import ReviewRepository
from app.repositories.user_preference_repository import UserPreferenceRepository
from app.schemas.book import BookResponse

logger = structlog.get_logger()


class RecommendationService:
    """Content-based recommendation engine using TF-IDF and cosine similarity.

    Algorithm:
    1. Build feature vectors from book metadata (genre, author, description).
    2. Apply TF-IDF vectorization.
    3. Construct a user profile vector from their borrow history weighted by ratings.
    4. Boost by explicit preferences (preferred_genres, preferred_authors).
    5. Rank unread books by cosine similarity to the user profile.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.book_repo = BookRepository(session)
        self.borrow_repo = BorrowRepository(session)
        self.review_repo = ReviewRepository(session)
        self.pref_repo = UserPreferenceRepository(session)

    async def get_recommendations(
        self, user_id: UUID, *, limit: int = 10
    ) -> tuple[list[BookResponse], str]:
        """Generate book recommendations for a user.

        Returns:
            Tuple of (recommended books, strategy description).
        """
        preferences = await self.pref_repo.get_by_user_id(user_id)
        borrows = await self.borrow_repo.get_all_for_user(user_id)
        borrowed_book_ids = {b.book_id for b in borrows}

        reviews = await self.review_repo.get_all_for_user(user_id)
        review_map = {r.book_id: r.rating for r in reviews}

        all_books = await self.book_repo.get_all_books()
        if not all_books:
            return [], "no_books_available"

        # Build feature strings for TF-IDF
        feature_strings = []
        for book in all_books:
            # Repeat genre and author to give them higher weight in TF-IDF
            features = (
                f"{book.genre} {book.genre} {book.genre} "
                f"{book.author} {book.author} "
                f"{book.description or ''}"
            )
            feature_strings.append(features)

        # TF-IDF vectorization
        vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
        tfidf_matrix = vectorizer.fit_transform(feature_strings)

        # Find indices of books the user has borrowed
        borrowed_indices = [
            i for i, book in enumerate(all_books) if book.id in borrowed_book_ids
        ]

        if borrowed_indices:
            # Build user profile from borrowed books, weighted by ratings
            weights = []
            for idx in borrowed_indices:
                book_id = all_books[idx].id
                rating = review_map.get(book_id, 3)  # neutral default
                weights.append(rating / 5.0)

            borrowed_vectors = tfidf_matrix[borrowed_indices].toarray()
            weight_array = np.array(weights)
            user_profile = np.average(borrowed_vectors, axis=0, weights=weight_array)
            strategy = "content_based_with_history"
        elif preferences and (preferences.preferred_genres or preferences.preferred_authors):
            # Cold start with explicit preferences
            pref_text = " ".join(
                (preferences.preferred_genres or []) + (preferences.preferred_authors or [])
            )
            user_profile = vectorizer.transform([pref_text]).toarray()[0]
            strategy = "content_based_with_preferences"
        else:
            # Truly cold start: return popular books
            popular = await self.book_repo.get_highly_rated(limit)
            return (
                [BookResponse.model_validate(b) for b in popular],
                "popular_fallback",
            )

        # Boost by explicit preferences
        if preferences and preferences.preferred_genres:
            genre_text = " ".join(preferences.preferred_genres)
            genre_vec = vectorizer.transform([genre_text]).toarray()[0]
            user_profile = user_profile + 0.3 * genre_vec

        if preferences and preferences.preferred_authors:
            author_text = " ".join(preferences.preferred_authors)
            author_vec = vectorizer.transform([author_text]).toarray()[0]
            user_profile = user_profile + 0.2 * author_vec

        # Compute cosine similarity
        similarities = cosine_similarity([user_profile], tfidf_matrix.toarray())[0]

        # Apply genre_weights to boost/penalize genres based on implicit preferences
        if preferences and preferences.genre_weights:
            for idx, book in enumerate(all_books):
                if book.genre in preferences.genre_weights:
                    # Scale similarity by genre weight
                    # 0.2 (1-star) → multiply by 0.2 (penalize heavily)
                    # 0.6 (3-star) → multiply by 0.6 (slight penalty)
                    # 1.0 (5-star) → multiply by 1.0 (no change)
                    similarities[idx] *= preferences.genre_weights[book.genre]

        # Zero out already-borrowed books
        for idx in borrowed_indices:
            similarities[idx] = -1.0

        # Get top-N
        top_indices = np.argsort(similarities)[::-1][:limit]
        recommended = [
            BookResponse.model_validate(all_books[i])
            for i in top_indices
            if similarities[i] > 0
        ]

        logger.info(
            "recommendations_generated",
            user_id=str(user_id),
            strategy=strategy,
            count=len(recommended),
        )
        return recommended, strategy

    async def update_implicit_preferences(self, user_id: UUID) -> None:
        """Recalculate genre_weights based on borrow history and ratings.

        Called after borrow, return, or review events to keep
        the implicit preference vector up-to-date.
        """
        preferences = await self.pref_repo.get_by_user_id(user_id)
        if not preferences:
            return

        borrows = await self.borrow_repo.get_all_for_user(user_id)
        reviews = await self.review_repo.get_all_for_user(user_id)
        review_map = {r.book_id: r.rating for r in reviews}

        genre_weights: dict[str, float] = {}
        genre_counts: dict[str, int] = {}

        for borrow in borrows:
            # Fetch the book to get its genre
            book = await self.book_repo.get_by_id(borrow.book_id)
            if not book:
                continue

            # Use rating to determine weight (absolute scale 0-1)
            if borrow.book_id in review_map:
                # Rating-based weight: 1 star = 0.2, 3 stars = 0.6, 5 stars = 1.0
                weight = review_map[borrow.book_id] / 5.0
            else:
                # Unrated books get neutral weight
                weight = 0.6

            genre_weights[book.genre] = genre_weights.get(book.genre, 0.0) + weight
            genre_counts[book.genre] = genre_counts.get(book.genre, 0) + 1

        # Average weights per genre (instead of normalizing to max)
        if genre_weights:
            genre_weights = {
                genre: round(genre_weights[genre] / genre_counts[genre], 3)
                for genre in genre_weights.keys()
            }

        preferences.genre_weights = genre_weights
        await self.pref_repo.update(preferences)

        logger.info(
            "implicit_preferences_updated",
            user_id=str(user_id),
            genre_count=len(genre_weights),
        )
