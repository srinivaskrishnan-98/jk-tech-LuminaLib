"""Recommendation controller handling personalized book recommendations."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.recommendation import RecommendationResponse
from app.services.recommendation_service import RecommendationService


class RecommendationController:
    """Controller for personalized recommendation endpoints."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.service = RecommendationService(session)

    async def get_recommendations(
        self, user: User, limit: int = 10
    ) -> RecommendationResponse:
        """Get personalized book recommendations for the user."""
        books, strategy = await self.service.get_recommendations(user.id, limit=limit)
        return RecommendationResponse(recommendations=books, strategy=strategy)
