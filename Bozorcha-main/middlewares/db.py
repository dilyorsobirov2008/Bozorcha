import logging
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Update
from database.engine import async_session

logger = logging.getLogger(__name__)

class DatabaseMiddleware(BaseMiddleware):
    """Middleware to inject SQLAlchemy async session into handler data."""
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        async with async_session() as session:
            data["session"] = session
            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception as e:
                await session.rollback()
                logger.exception("Database error occurred in middleware, transaction rolled back: %s", e)
                raise e
