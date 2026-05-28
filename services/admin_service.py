import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.admin import Admin


class AdminService:
    """Service layer for Admin authentication and management."""

    @staticmethod
    async def authenticate(
        session: AsyncSession, login: str, password: str
    ) -> Admin | None:
        """Authenticate an admin by login and password.

        Returns the Admin if credentials are valid, None otherwise.
        """
        result = await session.execute(
            select(Admin).where(Admin.login == login)
        )
        admin = result.scalar_one_or_none()
        if admin is None:
            return None

        if bcrypt.checkpw(
            password.encode("utf-8"), admin.password_hash.encode("utf-8")
        ):
            return admin
        return None

    @staticmethod
    async def create(
        session: AsyncSession, login: str, password: str
    ) -> Admin:
        """Create a new admin with a hashed password."""
        hashed = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        admin = Admin(login=login, password_hash=hashed)
        session.add(admin)
        await session.commit()
        await session.refresh(admin)
        return admin

    @staticmethod
    async def get_all(session: AsyncSession) -> list[Admin]:
        """Get all admins."""
        result = await session.execute(select(Admin).order_by(Admin.id))
        return list(result.scalars().all())

    @staticmethod
    async def delete(session: AsyncSession, admin_id: int) -> bool:
        """Delete an admin by id. Returns True if deleted."""
        result = await session.execute(
            select(Admin).where(Admin.id == admin_id)
        )
        admin = result.scalar_one_or_none()
        if admin is None:
            return False
        await session.delete(admin)
        await session.commit()
        return True
