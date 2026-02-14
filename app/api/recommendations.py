from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.recommendation import RecommendationResponse
from app.services.recommendation_service import RecommendationService

router = APIRouter()


@router.get("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(
    limit: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> RecommendationResponse:
    """Get ML-based book recommendations for the current user."""
    service = RecommendationService(session)
    books, strategy = await service.get_recommendations(current_user.id, limit=limit)
    return RecommendationResponse(recommendations=books, strategy=strategy)
