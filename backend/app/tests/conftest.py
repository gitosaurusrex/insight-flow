"""Test fixtures and configuration."""

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.main import app


# Use SQLite for tests
TEST_DB_URL = "sqlite+aiosqlite:///./test.db"
test_engine = create_async_engine(TEST_DB_URL, echo=False)
test_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create and tear down test database tables."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session():
    """Provide a test database session."""
    async with test_session() as session:
        yield session


async def override_get_db():
    """Override database dependency for tests."""
    async with test_session() as session:
        yield session


# Mock MongoDB
mock_mongo_db = MagicMock()
mock_collection = MagicMock()
mock_collection.insert_one = AsyncMock()
mock_collection.find_one = AsyncMock(return_value=None)
mock_collection.update_one = AsyncMock()
mock_collection.create_index = AsyncMock()
mock_mongo_db.feedback_content = mock_collection
mock_mongo_db.__getitem__ = MagicMock(return_value=mock_collection)

# Mock Redis
mock_redis = AsyncMock()
mock_redis.get = AsyncMock(return_value=None)
mock_redis.setex = AsyncMock()
mock_redis.delete = AsyncMock()


@pytest_asyncio.fixture(autouse=True)
async def mock_services():
    """Mock external services (MongoDB, Redis) for tests."""
    with (
        patch("app.core.database.mongo_db", mock_mongo_db),
        patch("app.core.database.get_mongo", return_value=mock_mongo_db),
        patch("app.core.database.redis_client", mock_redis),
        patch("app.core.database.get_redis", return_value=mock_redis),
        patch("app.core.database.init_mongo", new_callable=AsyncMock),
        patch("app.core.database.close_mongo", new_callable=AsyncMock),
        patch("app.core.database.init_redis", new_callable=AsyncMock),
        patch("app.core.database.close_redis", new_callable=AsyncMock),
    ):
        yield


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def client():
    """Provide an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient):
    """Register a user and return auth headers."""
    await client.post(
        "/api/auth/register",
        json={
            "email": f"test-{uuid.uuid4().hex[:8]}@example.com",
            "password": "testpassword123",
            "org_name": "Test Org",
        },
    )
    login_resp = await client.post(
        "/api/auth/login",
        json={
            "email": f"test-{uuid.uuid4().hex[:8]}@example.com",
            "password": "testpassword123",
        },
    )
    # Register a fresh user for reliable login
    email = f"auth-{uuid.uuid4().hex[:8]}@example.com"
    await client.post(
        "/api/auth/register",
        json={"email": email, "password": "testpass123", "org_name": "Auth Org"},
    )
    resp = await client.post(
        "/api/auth/login",
        json={"email": email, "password": "testpass123"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
