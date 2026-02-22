"""Database connections for PostgreSQL, MongoDB, and Redis."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from motor.motor_asyncio import AsyncIOMotorClient
from redis.asyncio import Redis

from app.core.config import settings

# --- PostgreSQL (SQLAlchemy async) ---
engine = create_async_engine(settings.async_database_url, echo=settings.DEBUG)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""
    pass


async def get_db() -> AsyncSession:
    """Yield an async database session."""
    async with async_session() as session:
        yield session


# --- MongoDB (Motor) ---
mongo_client: AsyncIOMotorClient = None
mongo_db = None


def get_mongo():
    """Return the MongoDB database instance."""
    return mongo_db


async def init_mongo() -> None:
    """Initialize MongoDB connection."""
    global mongo_client, mongo_db
    mongo_client = AsyncIOMotorClient(settings.mongo_connection_url)
    mongo_db = mongo_client[settings.MONGO_DB]
    # Ensure index on metadata_id
    await mongo_db.feedback_content.create_index("metadata_id", unique=True)


async def close_mongo() -> None:
    """Close MongoDB connection."""
    global mongo_client
    if mongo_client:
        mongo_client.close()


# --- Redis ---
redis_client: Redis = None


def get_redis() -> Redis:
    """Return the Redis client instance."""
    return redis_client


async def init_redis() -> None:
    """Initialize Redis connection."""
    global redis_client
    redis_client = Redis.from_url(settings.redis_connection_url, decode_responses=True)


async def close_redis() -> None:
    """Close Redis connection."""
    global redis_client
    if redis_client:
        await redis_client.close()
