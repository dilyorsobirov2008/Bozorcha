from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.base import Base
from models.category import Category


class CategoryService:
    """Service layer for Category CRUD operations."""

    @staticmethod
    async def get_all(session: AsyncSession) -> list[Category]:
        """Get all categories ordered by id."""
        result = await session.execute(
            select(Category).order_by(Category.id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(session: AsyncSession, category_id: int) -> Category | None:
        """Get a category by its id."""
        result = await session.execute(
            select(Category).where(Category.id == category_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        session: AsyncSession, name: str, image: str | None = None
    ) -> Category:
        """Create a new category."""
        category = Category(name=name, image=image)
        session.add(category)
        await session.commit()
        await session.refresh(category)
        return category

    @staticmethod
    async def update(
        session: AsyncSession,
        category_id: int,
        name: str | None = None,
        image: str | None = None,
    ) -> Category | None:
        """Update an existing category. Returns None if not found."""
        category = await CategoryService.get_by_id(session, category_id)
        if category is None:
            return None
        if name is not None:
            category.name = name
        if image is not None:
            category.image = image
        await session.commit()
        await session.refresh(category)
        return category

    @staticmethod
    async def delete(session: AsyncSession, category_id: int) -> bool:
        """Delete a category by id. Returns True if deleted."""
        category = await CategoryService.get_by_id(session, category_id)
        if category is None:
            return False
        await session.delete(category)
        await session.commit()
        return True
