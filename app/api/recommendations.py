from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.recommendation_controller import RecommendationController
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.recommendation import RecommendationResponse

router = APIRouter()


@router.get("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(
    limit: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> RecommendationResponse:
    """Get ML-based book recommendations for the current user."""
    controller = RecommendationController(session)
    return await controller.get_recommendations(current_user, limit=limit)
