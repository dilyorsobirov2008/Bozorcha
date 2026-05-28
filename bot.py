"""
Main bot entry-point.
Sets up the database, registers middlewares and handlers, and starts polling.
"""

import asyncio
import logging

from loader import bot, dp
from database.engine import engine, async_session
from database.base import Base
from handlers import register_all_handlers
from middlewares.db import DbSessionMiddleware
from middlewares.throttle import ThrottleMiddleware


async def on_startup() -> None:
    """Create all database tables and perform start-up tasks."""
    # Ensure every model is imported so SQLAlchemy sees them
    import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logging.info("Database tables created / verified")
    
    from services.admin_service import AdminService
    
    # Seed the requested admin credentials
    async with async_session() as session:
        try:
            admins = await AdminService.get_all(session)
            if not any(a.login == "Dilyor" for a in admins):
                await AdminService.create(session, login="Dilyor", password="dilyor2020")
                logging.info("Default admin 'Dilyor' created successfully!")
        except Exception as e:
            logging.error(f"Failed to seed default admin: {e}")



async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    await on_startup()

    # --- Middlewares (order matters) ---
    dp.message.middleware(DbSessionMiddleware())
    dp.callback_query.middleware(DbSessionMiddleware())
    dp.message.middleware(ThrottleMiddleware())

    # --- Handlers ---
    register_all_handlers(dp)

    logging.info("Bot started!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
