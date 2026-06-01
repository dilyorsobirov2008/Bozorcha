from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.category import Category


async def create_category(
    session: AsyncSession, name: str, emoji: str = "📁"
) -> Category:
    """Create a new category with auto-incrementing position."""
    # Determine next position
    stmt = select(func.coalesce(func.max(Category.position), 0))
    result = await session.execute(stmt)
    max_position = result.scalar_one()

    category = Category(
        name=name,
        emoji=emoji,
        position=max_position + 1,
        is_active=True,
    )
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category


async def get_categories(session: AsyncSession) -> list[Category]:
    """Get all active categories ordered by position."""
    stmt = (
        select(Category)
        .where(Category.is_active == True)
        .order_by(Category.position)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_category(session: AsyncSession, category_id: int) -> Category | None:
    """Get a single category by ID."""
    stmt = select(Category).where(Category.id == category_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def update_category(
    session: AsyncSession, category_id: int, **kwargs
) -> Category:
    """Update category fields."""
    stmt = select(Category).where(Category.id == category_id)
    result = await session.execute(stmt)
    category = result.scalar_one_or_none()

    if category is None:
        raise ValueError(f"Category with id={category_id} not found")

    for key, value in kwargs.items():
        if hasattr(category, key):
            setattr(category, key, value)

    await session.commit()
    await session.refresh(category)
    return category


async def delete_category(session: AsyncSession, category_id: int) -> bool:
    """Soft delete a category by setting is_active to False."""
    stmt = select(Category).where(Category.id == category_id)
    result = await session.execute(stmt)
    category = result.scalar_one_or_none()

    if category is None:
        return False

    category.is_active = False
    await session.commit()
    return True


async def count_categories(session: AsyncSession) -> int:
    """Count total active categories."""
    stmt = select(func.count(Category.id)).where(Category.is_active == True)
    result = await session.execute(stmt)
    return result.scalar_one()
