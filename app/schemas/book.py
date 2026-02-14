from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class BookCreate(BaseModel):
    title: str = Field(max_length=500)
    author: str = Field(max_length=255)
    isbn: str | None = Field(default=None, max_length=20)
    genre: str = Field(max_length=100)
    description: str | None = None
    total_copies: int = Field(default=1, ge=1)


class BookUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=500)
    author: str | None = Field(default=None, max_length=255)
    isbn: str | None = Field(default=None, max_length=20)
    genre: str | None = Field(default=None, max_length=100)
    description: str | None = None
    total_copies: int | None = Field(default=None, ge=1)


class BookResponse(BaseModel):
    id: UUID
    title: str
    author: str
    isbn: str | None
    genre: str
    description: str | None
    file_type: str
    summary: str | None
    summary_status: str
    review_consensus: str | None
    total_copies: int
    available_copies: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
