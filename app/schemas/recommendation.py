from pydantic import BaseModel

from app.schemas.book import BookResponse


class RecommendationResponse(BaseModel):
    recommendations: list[BookResponse]
    strategy: str
