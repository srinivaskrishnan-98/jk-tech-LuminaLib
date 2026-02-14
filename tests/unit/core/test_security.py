import pytest

from app.config import Settings
from app.core.exceptions import UnauthorizedException
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def get_settings() -> Settings:
    return Settings(
        JWT_SECRET_KEY="test-secret",
        JWT_ALGORITHM="HS256",
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30,
        DATABASE_URL="sqlite+aiosqlite:///./test.db",
    )


class TestPasswordHashing:
    def test_hash_password_returns_different_value(self) -> None:
        password = "MySecurePassword123"
        hashed = hash_password(password)
        assert hashed != password
        assert hashed.startswith("$2b$")

    def test_verify_correct_password(self) -> None:
        password = "MySecurePassword123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_wrong_password(self) -> None:
        hashed = hash_password("CorrectPassword")
        assert verify_password("WrongPassword", hashed) is False

    def test_different_hashes_for_same_password(self) -> None:
        password = "SamePassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2  # bcrypt uses random salt


class TestJWT:
    def test_create_access_token_returns_tuple(self) -> None:
        settings = get_settings()
        token, jti, expires = create_access_token("user-123", settings)
        assert isinstance(token, str)
        assert isinstance(jti, str)
        assert expires is not None

    def test_decode_valid_token(self) -> None:
        settings = get_settings()
        token, jti, _ = create_access_token("user-123", settings)
        payload = decode_access_token(token, settings)
        assert payload["sub"] == "user-123"
        assert payload["jti"] == jti

    def test_decode_invalid_token_raises(self) -> None:
        settings = get_settings()
        with pytest.raises(UnauthorizedException):
            decode_access_token("invalid-token", settings)

    def test_decode_token_with_wrong_secret_raises(self) -> None:
        settings = get_settings()
        token, _, _ = create_access_token("user-123", settings)
        wrong_settings = Settings(
            JWT_SECRET_KEY="wrong-secret",
            DATABASE_URL="sqlite+aiosqlite:///./test.db",
        )
        with pytest.raises(UnauthorizedException):
            decode_access_token(token, wrong_settings)

    def test_token_contains_extra_claims(self) -> None:
        settings = get_settings()
        token, _, _ = create_access_token(
            "user-123", settings, extra_claims={"role": "admin"}
        )
        payload = decode_access_token(token, settings)
        assert payload["role"] == "admin"
