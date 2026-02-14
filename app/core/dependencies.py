from functools import lru_cache

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.core.database import get_db
from app.interfaces.llm import LLMProvider
from app.interfaces.storage import StorageBackend
from app.models.user import User
from app.services.auth_service import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@lru_cache
def get_settings() -> Settings:
    """Cached application settings."""
    return Settings()


def get_auth_service(
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AuthService:
    return AuthService(session, settings)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    """FastAPI dependency that extracts and validates the current user from JWT."""
    auth_service = AuthService(session, settings)
    return await auth_service.validate_token(token)


def get_storage_backend(
    settings: Settings = Depends(get_settings),
) -> StorageBackend:
    """Resolve the storage backend based on configuration."""
    from app.infrastructure.storage.factory import create_storage_backend

    return create_storage_backend(settings)


def get_llm_provider(
    settings: Settings = Depends(get_settings),
) -> LLMProvider:
    """Resolve the LLM provider based on configuration."""
    from app.infrastructure.llm.factory import create_llm_provider

    return create_llm_provider(settings)
