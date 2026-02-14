import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.core.exceptions import InvalidCredentialsException, UserAlreadyExistsException
from app.schemas.auth import LoginRequest, SignupRequest
from app.services.auth_service import AuthService


def get_settings() -> Settings:
    return Settings(
        JWT_SECRET_KEY="test-secret",
        DATABASE_URL="sqlite+aiosqlite:///./test.db",
    )


@pytest.mark.asyncio
class TestAuthServiceSignup:
    async def test_signup_creates_user(self, db_session: AsyncSession) -> None:
        service = AuthService(db_session, get_settings())
        data = SignupRequest(
            email="new@example.com",
            username="newuser",
            password="SecurePass123",
            full_name="New User",
            preferred_genres=["Fiction"],
        )
        result = await service.signup(data)
        assert result.email == "new@example.com"
        assert result.username == "newuser"
        assert result.preferred_genres == ["Fiction"]

    async def test_signup_duplicate_email_raises(
        self, db_session: AsyncSession, test_user,
    ) -> None:
        service = AuthService(db_session, get_settings())
        data = SignupRequest(
            email="test@example.com",  # Same as test_user
            username="differentuser",
            password="SecurePass123",
        )
        with pytest.raises(UserAlreadyExistsException):
            await service.signup(data)

    async def test_signup_duplicate_username_raises(
        self, db_session: AsyncSession, test_user,
    ) -> None:
        service = AuthService(db_session, get_settings())
        data = SignupRequest(
            email="different@example.com",
            username="testuser",  # Same as test_user
            password="SecurePass123",
        )
        with pytest.raises(UserAlreadyExistsException):
            await service.signup(data)


@pytest.mark.asyncio
class TestAuthServiceLogin:
    async def test_login_returns_token(self, db_session: AsyncSession, test_user) -> None:
        service = AuthService(db_session, get_settings())
        data = LoginRequest(email="test@example.com", password="TestPass123")
        result = await service.login(data)
        assert result.access_token is not None
        assert result.token_type == "bearer"

    async def test_login_wrong_password_raises(self, db_session: AsyncSession, test_user) -> None:
        service = AuthService(db_session, get_settings())
        data = LoginRequest(email="test@example.com", password="WrongPassword")
        with pytest.raises(InvalidCredentialsException):
            await service.login(data)

    async def test_login_nonexistent_user_raises(self, db_session: AsyncSession) -> None:
        service = AuthService(db_session, get_settings())
        data = LoginRequest(email="nobody@example.com", password="Password123")
        with pytest.raises(InvalidCredentialsException):
            await service.login(data)
