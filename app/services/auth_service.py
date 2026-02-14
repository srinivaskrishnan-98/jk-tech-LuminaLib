from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.core.exceptions import (
    InvalidCredentialsException,
    TokenRevokedException,
    UnauthorizedException,
    UserAlreadyExistsException,
)
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.models.blacklisted_token import BlacklistedToken
from app.models.user import User
from app.models.user_preference import UserPreference
from app.repositories.blacklisted_token_repository import BlacklistedTokenRepository
from app.repositories.user_preference_repository import UserPreferenceRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    LoginRequest,
    ProfileUpdateRequest,
    SignupRequest,
    TokenResponse,
    UserProfileResponse,
)

logger = structlog.get_logger()


class AuthService:
    """Handles user authentication and profile management."""

    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.user_repo = UserRepository(session)
        self.token_repo = BlacklistedTokenRepository(session)
        self.pref_repo = UserPreferenceRepository(session)

    async def signup(self, data: SignupRequest) -> UserProfileResponse:
        """Register a new user with optional genre/author preferences."""
        logger.info("signup_attempt", email=data.email, username=data.username)

        if await self.user_repo.email_exists(data.email):
            raise UserAlreadyExistsException("email")
        if await self.user_repo.username_exists(data.username):
            raise UserAlreadyExistsException("username")

        user = User(
            email=data.email,
            username=data.username,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
        )
        user = await self.user_repo.create(user)

        # Create user preferences
        preference = UserPreference(
            user_id=user.id,
            preferred_genres=data.preferred_genres,
            preferred_authors=data.preferred_authors,
            genre_weights={},
        )
        await self.pref_repo.create(preference)

        logger.info("user_registered", user_id=str(user.id))
        return self._build_profile_response(user, preference)

    async def login(self, data: LoginRequest) -> TokenResponse:
        """Authenticate user and return JWT token."""
        logger.info("login_attempt", email=data.email)

        user = await self.user_repo.get_by_email(data.email)
        if not user or not verify_password(data.password, user.hashed_password):
            raise InvalidCredentialsException()

        if not user.is_active:
            raise UnauthorizedException("Account is deactivated")

        token, _jti, _expires = create_access_token(
            subject=str(user.id), settings=self.settings
        )

        logger.info("user_logged_in", user_id=str(user.id))
        return TokenResponse(access_token=token)

    async def signout(self, token: str, user_id: UUID) -> None:
        """Revoke the current JWT token by blacklisting its JTI."""
        payload = decode_access_token(token, self.settings)
        jti = payload.get("jti")
        exp = payload.get("exp")

        if not jti or not exp:
            raise UnauthorizedException("Invalid token structure")

        blacklisted = BlacklistedToken(
            token_jti=jti,
            user_id=user_id,
            expires_at=datetime.fromtimestamp(exp, tz=UTC),
        )
        await self.token_repo.create(blacklisted)
        logger.info("user_signed_out", user_id=str(user_id), jti=jti)

    async def get_profile(self, user_id: UUID) -> UserProfileResponse:
        """Get user profile with preferences."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UnauthorizedException("User not found")

        preference = await self.pref_repo.get_by_user_id(user_id)
        return self._build_profile_response(user, preference)

    async def update_profile(
        self, user_id: UUID, data: ProfileUpdateRequest
    ) -> UserProfileResponse:
        """Update user profile and/or preferences."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UnauthorizedException("User not found")

        if data.full_name is not None:
            user.full_name = data.full_name
        await self.user_repo.update(user)

        preference = await self.pref_repo.get_by_user_id(user_id)
        if preference:
            if data.preferred_genres is not None:
                preference.preferred_genres = data.preferred_genres
            if data.preferred_authors is not None:
                preference.preferred_authors = data.preferred_authors
            await self.pref_repo.update(preference)

        logger.info("profile_updated", user_id=str(user_id))
        return self._build_profile_response(user, preference)

    async def validate_token(self, token: str) -> User:
        """Validate token and return the user. Used by get_current_user dependency."""
        payload = decode_access_token(token, self.settings)
        jti = payload.get("jti")

        if jti and await self.token_repo.is_blacklisted(jti):
            raise TokenRevokedException()

        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedException("Invalid token: missing subject")

        user = await self.user_repo.get_by_id(UUID(user_id))
        if not user or not user.is_active:
            raise UnauthorizedException("User not found or inactive")

        return user

    @staticmethod
    def _build_profile_response(
        user: User, preference: UserPreference | None
    ) -> UserProfileResponse:
        return UserProfileResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            preferred_genres=preference.preferred_genres if preference else [],
            preferred_authors=preference.preferred_authors if preference else [],
        )
