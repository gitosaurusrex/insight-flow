"""Organization repository for database operations."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization


async def create_organization(
    db: AsyncSession, name: str, owner_id: uuid.UUID
) -> Organization:
    """Create a new organization."""
    org = Organization(name=name, owner_id=owner_id)
    db.add(org)
    await db.flush()
    return org


async def get_organization_by_id(
    db: AsyncSession, org_id: uuid.UUID
) -> Organization | None:
    """Fetch an organization by ID."""
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    return result.scalar_one_or_none()


async def get_user_organizations(
    db: AsyncSession, user_id: uuid.UUID
) -> list[Organization]:
    """Fetch all organizations owned by a user."""
    result = await db.execute(
        select(Organization).where(Organization.owner_id == user_id)
    )
    return list(result.scalars().all())
