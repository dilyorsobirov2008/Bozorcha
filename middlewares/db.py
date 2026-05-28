from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from database.engine import async_session


class DbSessionMiddleware(BaseMiddleware):
    """Middleware that injects an async database session into handler data.

    Creates a new AsyncSession for each incoming update and ensures
    it is properly closed after the handler completes.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async with async_session() as session:
            data["session"] = session
            try:
                return await handler(event, data)
            finally:
                await session.close()
