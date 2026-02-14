from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    review_text: str = Field(min_length=10, max_length=5000)


class ReviewResponse(BaseModel):
    id: UUID
    user_id: UUID
    book_id: UUID
    rating: int
    review_text: str
    sentiment_score: float | None
    created_at: datetime

    model_config = {"from_attributes": True}


class BookAnalysisResponse(BaseModel):
    book_id: UUID
    title: str
    review_consensus: str | None
    total_reviews: int
    average_rating: float | None
    rating_distribution: dict[str, int]
