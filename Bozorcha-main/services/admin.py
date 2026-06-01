import bcrypt
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.admin import Admin


async def authenticate_admin(
    session: AsyncSession, username: str, password: str
) -> Admin | None:
    """Authenticate admin by username and password using bcrypt."""
    stmt = select(Admin).where(Admin.username == username, Admin.is_active == True)
    result = await session.execute(stmt)
    admin = result.scalar_one_or_none()

    if admin is None:
        return None

    if bcrypt.checkpw(password.encode("utf-8"), admin.password_hash.encode("utf-8")):
        return admin

    return None


async def get_admin(session: AsyncSession, telegram_id: int) -> Admin | None:
    """Get admin by Telegram ID."""
    stmt = select(Admin).where(
        Admin.telegram_id == telegram_id, Admin.is_active == True
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_admin(
    session: AsyncSession,
    telegram_id: int,
    username: str,
    password: str,
) -> Admin:
    """Create a new admin with bcrypt-hashed password."""
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    admin = Admin(
        telegram_id=telegram_id,
        username=username,
        password_hash=password_hash,
        is_active=True,
    )
    session.add(admin)
    await session.commit()
    await session.refresh(admin)
    return admin


async def get_all_admins(session: AsyncSession) -> list[Admin]:
    """Get all active admins."""
    stmt = select(Admin).where(Admin.is_active == True).order_by(Admin.id)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def delete_admin(session: AsyncSession, admin_id: int) -> bool:
    """Soft-delete an admin by setting is_active to False."""
    stmt = select(Admin).where(Admin.id == admin_id)
    result = await session.execute(stmt)
    admin = result.scalar_one_or_none()

    if admin is None:
        return False

    admin.is_active = False
    await session.commit()
    return True


async def is_admin(session: AsyncSession, telegram_id: int) -> bool:
    """Check if a user is an active admin in the database."""
    stmt = select(func.count(Admin.id)).where(
        Admin.telegram_id == telegram_id, Admin.is_active == True
    )
    result = await session.execute(stmt)
    return result.scalar_one() > 0
