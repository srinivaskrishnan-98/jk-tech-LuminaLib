import asyncio
import os
from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings
from app.core.database import get_db

# Register JSONB as JSON for SQLite (used in tests)
SQLiteTypeCompiler.visit_JSONB = lambda self, type_, **kw: "JSON"
from app.core.dependencies import (
    get_current_user,
    get_llm_provider,
    get_settings,
    get_storage_backend,
)
from app.core.security import create_access_token, hash_password
from app.infrastructure.llm.mock_provider import MockLLMProvider
from app.interfaces.storage import StorageBackend
from app.main import create_app
from app.models.base import Base
from app.models.user import User
from app.models.user_preference import UserPreference

# Use SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


def get_test_settings() -> Settings:
    return Settings(
        DATABASE_URL=TEST_DATABASE_URL,
        JWT_SECRET_KEY="test-secret-key",
        STORAGE_BACKEND="local",
        LOCAL_STORAGE_PATH="/tmp/luminalib-test-uploads",
        LLM_PROVIDER="mock",
    )


class InMemoryStorage(StorageBackend):
    """In-memory storage backend for testing."""

    def __init__(self) -> None:
        self._files: dict[str, bytes] = {}

    async def upload_file(self, file_content, file_key: str, content_type: str) -> str:
        content = file_content.read() if hasattr(file_content, "read") else file_content
        self._files[file_key] = content
        return file_key

    async def download_file(self, file_key: str) -> bytes:
        if file_key not in self._files:
            raise FileNotFoundError(f"File not found: {file_key}")
        return self._files[file_key]

    async def delete_file(self, file_key: str) -> None:
        self._files.pop(file_key, None)

    async def file_exists(self, file_key: str) -> bool:
        return file_key in self._files


@pytest_asyncio.fixture
async def db_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    # Clean up test DB file
    if os.path.exists("./test.db"):
        os.remove("./test.db")


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional database session for tests."""
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        id=uuid4(),
        email="test@example.com",
        username="testuser",
        hashed_password=hash_password("TestPass123"),
        full_name="Test User",
    )
    db_session.add(user)
    pref = UserPreference(
        user_id=user.id,
        preferred_genres=["Fiction", "Science"],
        preferred_authors=["Author A"],
        genre_weights={},
    )
    db_session.add(pref)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_storage() -> InMemoryStorage:
    return InMemoryStorage()


@pytest_asyncio.fixture
async def test_llm() -> MockLLMProvider:
    return MockLLMProvider()


@pytest_asyncio.fixture
async def auth_token(test_user: User) -> str:
    """Generate a JWT token for the test user."""
    settings = get_test_settings()
    token, _jti, _exp = create_access_token(str(test_user.id), settings)
    return token


@pytest_asyncio.fixture
async def client(
    db_session: AsyncSession,
    test_user: User,
    test_storage: InMemoryStorage,
    test_llm: MockLLMProvider,
    auth_token: str,
) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client with dependency overrides."""
    app = create_app()

    async def override_get_db():
        yield db_session

    async def override_get_current_user():
        return test_user

    def override_get_settings():
        return get_test_settings()

    def override_get_storage():
        return test_storage

    def override_get_llm():
        return test_llm

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_settings] = override_get_settings
    app.dependency_overrides[get_storage_backend] = override_get_storage
    app.dependency_overrides[get_llm_provider] = override_get_llm

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
