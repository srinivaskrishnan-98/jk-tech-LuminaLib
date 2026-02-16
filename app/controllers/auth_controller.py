"""Authentication controller handling user auth operations."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    ProfileUpdateRequest,
    SignupRequest,
    TokenResponse,
    UserProfileResponse,
)
from app.schemas.common import MessageResponse
from app.services.auth_service import AuthService


class AuthController:
    """Controller for authentication and user management endpoints."""

    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.service = AuthService(session, settings)

    async def signup(self, data: SignupRequest) -> UserProfileResponse:
        """Register a new user account."""
        return await self.service.signup(data)

    async def login(self, data: LoginRequest) -> TokenResponse:
        """Authenticate and receive a JWT access token."""
        return await self.service.login(data)

    async def signout(self, token: str, user_id) -> MessageResponse:
        """Revoke the current JWT token."""
        await self.service.signout(token, user_id)
        return MessageResponse(message="Successfully signed out")

    async def get_profile(self, user: User) -> UserProfileResponse:
        """Get current user's profile."""
        return await self.service.get_profile(user.id)

    async def update_profile(
        self, user: User, data: ProfileUpdateRequest
    ) -> UserProfileResponse:
        """Update user profile information."""
        return await self.service.update_profile(user.id, data)
