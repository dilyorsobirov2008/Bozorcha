from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User


class UserService:
    """Service layer for User operations."""

    @staticmethod
    async def get_or_create(
        session: AsyncSession, telegram_id: int, full_name: str
    ) -> User:
        """Get an existing user or create a new one. Updates name if exists."""
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if user is not None:
            user.full_name = full_name
            await session.commit()
            await session.refresh(user)
            return user

        user = User(telegram_id=telegram_id, full_name=full_name)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    @staticmethod
    async def update_phone(
        session: AsyncSession, telegram_id: int, phone: str
    ) -> User:
        """Update the phone number for a user identified by telegram_id."""
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one()
        user.phone = phone
        await session.commit()
        await session.refresh(user)
        return user

    @staticmethod
    async def update_language(
        session: AsyncSession, telegram_id: int, language: str
    ) -> User:
        """Update the preferred language for a user."""
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one()
        user.language = language
        await session.commit()
        await session.refresh(user)
        return user

    @staticmethod
    async def get_all_ids(session: AsyncSession) -> list[int]:
        """Return all telegram_ids for broadcast purposes."""
        result = await session.execute(select(User.telegram_id))
        return list(result.scalars().all())

    @staticmethod
    async def count(session: AsyncSession) -> int:
        """Count total registered users."""
        result = await session.execute(select(func.count(User.id)))
        return result.scalar_one()
