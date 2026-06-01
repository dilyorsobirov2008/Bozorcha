import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config.settings import settings
from database.engine import engine
from database.base import Base
from handlers.user import user_router
from handlers.admin import admin_router
from middlewares.db import DatabaseMiddleware
from middlewares.throttle import ThrottleMiddleware
from utils.logging_config import setup_logging

async def health_check(request):
    return web.Response(text="Bot is running smoothly!", status=200)

async def start_health_check_server() -> None:
    port = int(os.environ.get("PORT", 8080))
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"⚡ Health check server successfully started on port {port}")


async def auto_migrate() -> None:
    try:
        from alembic.config import Config
        from alembic import command
        import sqlalchemy as sa
        
        logging.info("⏳ Running programmatic database migrations...")
        
        # 1. Check if 'users' table exists, and if 'alembic_version' is missing
        async with engine.begin() as conn:
            from sqlalchemy import inspect
            def check_tables(connection):
                inspector = inspect(connection)
                has_users = "users" in inspector.get_table_names()
                has_alembic = "alembic_version" in inspector.get_table_names()
                return has_users, has_alembic
            
            has_users, has_alembic = await conn.run_sync(check_tables)
            
            # 2. If 'users' exists but 'alembic' does not, stamp '001'
            if has_users and not has_alembic:
                logging.info("⚠️ Detected existing tables without Alembic. Stamping revision '001'...")
                try:
                    await conn.execute(sa.text(
                        "CREATE TABLE alembic_version ("
                        "version_num VARCHAR(32) NOT NULL, "
                        "CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)"
                        ")"
                    ))
                    await conn.execute(sa.text("INSERT INTO alembic_version (version_num) VALUES ('001')"))
                    logging.info("✅ Database stamped to '001' successfully.")
                except Exception as stamp_err:
                    logging.warning(f"Could not stamp database: {stamp_err}")

        # 3. Run alembic upgrade head
        def run_upgrade():
            alembic_cfg = Config("alembic.ini")
            alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
            command.upgrade(alembic_cfg, "head")
            
        await asyncio.to_thread(run_upgrade)
        logging.info("🚀 Database migrations completed successfully.")

        # 3.5. Heal database schema by adding any missing columns to existing tables
        async with engine.begin() as conn:
            from sqlalchemy import inspect
            def heal_database_schema(connection):
                inspector = inspect(connection)
                tables = inspector.get_table_names()
                
                # Check categories table
                if "categories" in tables:
                    cols = [c["name"] for c in inspector.get_columns("categories")]
                    if "emoji" not in cols:
                        connection.execute(sa.text("ALTER TABLE categories ADD COLUMN emoji VARCHAR(10) DEFAULT '📁' NOT NULL"))
                        logging.info("Healed: Added emoji column to categories table.")
                    if "position" not in cols:
                        connection.execute(sa.text("ALTER TABLE categories ADD COLUMN position INTEGER DEFAULT 0 NOT NULL"))
                        logging.info("Healed: Added position column to categories table.")
                    if "is_active" not in cols:
                        connection.execute(sa.text("ALTER TABLE categories ADD COLUMN is_active BOOLEAN DEFAULT true NOT NULL"))
                        logging.info("Healed: Added is_active column to categories table.")
                    if "created_at" not in cols:
                        connection.execute(sa.text("ALTER TABLE categories ADD COLUMN created_at TIMESTAMP DEFAULT NOW() NOT NULL"))
                        logging.info("Healed: Added created_at column to categories table.")

                # Check products table
                if "products" in tables:
                    cols = [c["name"] for c in inspector.get_columns("products")]
                    if "is_active" not in cols:
                        connection.execute(sa.text("ALTER TABLE products ADD COLUMN is_active BOOLEAN DEFAULT true NOT NULL"))
                        logging.info("Healed: Added is_active column to products table.")
                    if "photo_id" not in cols:
                        connection.execute(sa.text("ALTER TABLE products ADD COLUMN photo_id VARCHAR(255) NULL"))
                        logging.info("Healed: Added photo_id column to products table.")
                    if "stock" not in cols:
                        connection.execute(sa.text("ALTER TABLE products ADD COLUMN stock INTEGER DEFAULT 0 NOT NULL"))
                        logging.info("Healed: Added stock column to products table.")
                    if "created_at" not in cols:
                        connection.execute(sa.text("ALTER TABLE products ADD COLUMN created_at TIMESTAMP DEFAULT NOW() NOT NULL"))
                        logging.info("Healed: Added created_at column to products table.")

                # Check users table
                if "users" in tables:
                    cols = [c["name"] for c in inspector.get_columns("users")]
                    if "created_at" not in cols:
                        connection.execute(sa.text("ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT NOW() NOT NULL"))
                        logging.info("Healed: Added created_at column to users table.")

                # Check admins table
                if "admins" in tables:
                    cols = [c["name"] for c in inspector.get_columns("admins")]
                    if "username" not in cols:
                        connection.execute(sa.text("ALTER TABLE admins ADD COLUMN username VARCHAR(100) DEFAULT 'admin' NOT NULL UNIQUE"))
                        logging.info("Healed: Added username column to admins table.")
                    if "password_hash" not in cols:
                        connection.execute(sa.text("ALTER TABLE admins ADD COLUMN password_hash VARCHAR(255) DEFAULT '' NOT NULL"))
                        logging.info("Healed: Added password_hash column to admins table.")
                    if "is_active" not in cols:
                        connection.execute(sa.text("ALTER TABLE admins ADD COLUMN is_active BOOLEAN DEFAULT true NOT NULL"))
                        logging.info("Healed: Added is_active column to admins table.")
                    if "created_at" not in cols:
                        connection.execute(sa.text("ALTER TABLE admins ADD COLUMN created_at TIMESTAMP DEFAULT NOW() NOT NULL"))
                        logging.info("Healed: Added created_at column to admins table.")
                    if "telegram_id" not in cols:
                        connection.execute(sa.text("ALTER TABLE admins ADD COLUMN telegram_id BIGINT DEFAULT 0 NOT NULL"))
                        logging.info("Healed: Added telegram_id column to admins table.")
                    if "updated_at" not in cols:
                        connection.execute(sa.text("ALTER TABLE admins ADD COLUMN updated_at TIMESTAMP NULL"))
                        logging.info("Healed: Added updated_at column to admins table.")

            await conn.run_sync(heal_database_schema)
            logging.info("✅ Database schema self-healing check passed successfully.")

        # 4. Seed default admin Dilyor if not exists
        async def seed_admin():
            from services.admin import create_admin
            from sqlalchemy import select
            from models.admin import Admin
            from database.engine import async_session
            
            logging.info("⏳ Checking if admin user Dilyor exists...")
            async with async_session() as session_factory:
                stmt = select(Admin).where(Admin.username == "Dilyor")
                res = await session_factory.execute(stmt)
                admin = res.scalar_one_or_none()
                
                if admin is None:
                    logging.info("👤 Creating default admin Dilyor...")
                    await create_admin(
                        session=session_factory,
                        telegram_id=7351189083, # User's exact Telegram ID from logs
                        username="Dilyor",
                        password="dilyor2020"
                    )
                    logging.info("✅ Default admin Dilyor successfully created!")
                else:
                    logging.info("👤 Admin Dilyor already exists.")
                    
        await seed_admin()
    except Exception as e:
        logging.critical(f"❌ Error during auto-migration: {e}")
        raise e

async def on_startup(bot: Bot) -> None:
    try:
        await auto_migrate()
        logging.info("🤖 Telegram Bot has been started!")
    except Exception as db_err:
        logging.critical("❌ Ma'lumotlar bazasiga ulanib yoki migratsiya qilib bo'lmadi!")
        logging.critical(f"Xatolik tafsiloti: {db_err}")
        raise db_err


async def on_shutdown(bot: Bot) -> None:
    await engine.dispose()
    logging.info("💤 Database engine connection closed.")
    logging.info("🛑 Telegram Bot stopped.")

async def main() -> None:
    # 1. Setup Logging
    setup_logging()
    
    # 2. Check Bot Token & Database configuration
    import sys
    if not settings.BOT_TOKEN or settings.BOT_TOKEN == "":
        logging.critical("❌ ERROR: BOT_TOKEN is missing! Buni Render Environment Variables-ga qo'shishingiz kerak!")
        logging.critical("Render Sozlamalari -> Environment Variables -> BOT_TOKEN ni o'rnating.")
        sys.exit(1)

    if "localhost" in settings.DATABASE_URL:
        logging.critical("❌ ERROR: DATABASE_URL hali sozlanmagan yoki localhost rejimida!")
        logging.critical("Render-da PostgreSQL ma'lumotlar bazasini yarating va uning 'External Database URL' manzilini")
        logging.critical("Render Sozlamalari -> Environment Variables -> DATABASE_URL ga o'rnating.")
        sys.exit(1)

    # 3. Initialize Bot & Dispatcher
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())
    
    # 4. Register Middlewares
    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())
    dp.message.middleware(ThrottleMiddleware())
    
    # 5. Global Error Handler to prevent bot crashes on unhandled handler errors
    @dp.errors()
    async def global_error_handler(event, exception):
        logging.error(f"⚠️ Unhandled error during update processing: {exception}", exc_info=True)
        return True

    # 6. Register Routers
    dp.include_router(user_router)
    dp.include_router(admin_router)
    
    # 7. Startup/Shutdown Hooks
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # 8. Start Health Check Server if PORT is specified (useful for Render Web Service)
    port_env = os.environ.get("PORT")
    if port_env:
        logging.info(f"Detected PORT={port_env}. Starting health check server...")
        asyncio.create_task(start_health_check_server())
        
    # 9. Start Polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot execution interrupted.")
    except Exception as global_err:
        logging.critical(f"🔥 Global uncaught exception in bot: {global_err}", exc_info=True)

