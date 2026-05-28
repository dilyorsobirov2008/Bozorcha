"""
Main bot entry-point.
Sets up the database, registers middlewares and handlers, and starts polling.
"""

import asyncio
import logging
import os
from aiohttp import web

from loader import bot, dp
from database.engine import engine, async_session
from database.base import Base
from handlers import register_all_handlers
from middlewares.db import DbSessionMiddleware
from middlewares.throttle import ThrottleMiddleware


async def start_dummy_server() -> None:
    """Start a dummy web server to satisfy Render's health check on Web Services."""
    port = int(os.environ.get("PORT", 8080))
    app = web.Application()
    
    async def handle(request):
        return web.Response(text="Bot is running!")
        
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"Dummy web server started on port {port}")


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

    # Start dummy web server to prevent Render from force-killing the Web Service
    try:
        await start_dummy_server()
    except Exception as e:
        logging.warning(f"Failed to start dummy web server: {e}")

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
