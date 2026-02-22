"""Authentication service layer."""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password, create_access_token
from app.repositories import user_repo, organization_repo
from app.schemas.user import UserRegister, UserLogin, TokenResponse, UserResponse


async def register_user(db: AsyncSession, data: UserRegister) -> UserResponse:
    """Register a new user and create their default organization."""
    existing = await user_repo.get_user_by_email(db, data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = await user_repo.create_user(db, data.email, hash_password(data.password))
    await organization_repo.create_organization(db, data.org_name, user.id)
    await db.commit()
    return UserResponse.model_validate(user)


async def login_user(db: AsyncSession, data: UserLogin) -> TokenResponse:
    """Authenticate a user and return a JWT token."""
    user = await user_repo.get_user_by_email(db, data.email)
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)
