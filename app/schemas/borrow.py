from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class BorrowResponse(BaseModel):
    id: UUID
    user_id: UUID
    book_id: UUID
    borrowed_at: datetime
    returned_at: datetime | None
    is_active: bool

    model_config = {"from_attributes": True}
