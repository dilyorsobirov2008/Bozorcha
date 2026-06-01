from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    full_name: str,
    username: str | None = None,
) -> User:
    """Get existing user or create a new one."""
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            telegram_id=telegram_id,
            full_name=full_name,
            username=username,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    else:
        # Update name/username if changed
        changed = False
        if user.full_name != full_name:
            user.full_name = full_name
            changed = True
        if user.username != username:
            user.username = username
            changed = True
        if changed:
            await session.commit()
            await session.refresh(user)

    return user


async def get_user(session: AsyncSession, telegram_id: int) -> User | None:
    """Get user by Telegram ID."""
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    """Get user by internal database ID."""
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def update_user_phone(
    session: AsyncSession, telegram_id: int, phone: str
) -> User:
    """Update user's phone number."""
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise ValueError(f"User with telegram_id={telegram_id} not found")

    user.phone = phone
    await session.commit()
    await session.refresh(user)
    return user


async def get_all_users(session: AsyncSession) -> list[User]:
    """Get all registered users."""
    stmt = select(User).order_by(User.id)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def count_users(session: AsyncSession) -> int:
    """Count total registered users."""
    stmt = select(func.count(User.id))
    result = await session.execute(stmt)
    return result.scalar_one()
