"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    APP_NAME: str = "InsightFlow"
    DEBUG: bool = False

    # PostgreSQL — supports Render's DATABASE_URL or individual vars
    DATABASE_URL: str | None = None
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "insightflow"
    POSTGRES_PASSWORD: str = "insightflow"
    POSTGRES_DB: str = "insightflow"

    @property
    def async_database_url(self) -> str:
        """Async database URL for SQLAlchemy (asyncpg driver)."""
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            # Render provides postgresql:// — convert for asyncpg
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql://", 1)
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def sync_database_url(self) -> str:
        """Sync database URL for Alembic and Celery tasks."""
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql://", 1)
            # Strip asyncpg driver if present
            return url.replace("postgresql+asyncpg://", "postgresql://", 1)
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # MongoDB — supports full MONGO_URL (for Atlas) or host/port
    MONGO_URL: str | None = None
    MONGO_HOST: str = "mongo"
    MONGO_PORT: int = 27017
    MONGO_DB: str = "insightflow"

    @property
    def mongo_connection_url(self) -> str:
        """MongoDB connection URL."""
        if self.MONGO_URL:
            return self.MONGO_URL
        return f"mongodb://{self.MONGO_HOST}:{self.MONGO_PORT}"

    # Redis — supports full REDIS_URL or host/port
    REDIS_URL: str | None = None
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379

    @property
    def redis_connection_url(self) -> str:
        """Redis connection URL."""
        if self.REDIS_URL:
            return self.REDIS_URL
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    # JWT
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Celery
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    # Cache
    CACHE_TTL: int = 300  # 5 minutes

    # CORS — comma-separated allowed origins for deployment
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
