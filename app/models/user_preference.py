import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin


class UserPreference(UUIDPrimaryKeyMixin, Base):
    """Hybrid user preference model combining explicit and implicit signals.

    - preferred_genres / preferred_authors: Explicit preferences set by the user.
    - genre_weights: Implicit preferences auto-computed from borrow history and ratings.
    """

    __tablename__ = "user_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    # Explicit preferences (user-set)
    preferred_genres: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    preferred_authors: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    # Implicit preferences (auto-computed from borrow history + ratings)
    genre_weights: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="preference")
