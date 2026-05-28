import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message


class ThrottleMiddleware(BaseMiddleware):
    """Simple rate-limiting middleware.

    Skips processing if the same user sends a message within the
    configured cooldown period (default 0.5 seconds).
    """

    def __init__(self, cooldown: float = 0.5) -> None:
        super().__init__()
        self.cooldown = cooldown
        self._last_message_time: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id if event.from_user else None
        if user_id is None:
            return await handler(event, data)

        now = time.monotonic()
        last_time = self._last_message_time.get(user_id)

        if last_time is not None and (now - last_time) < self.cooldown:
            # Throttled — skip this message
            return None

        self._last_message_time[user_id] = now
        return await handler(event, data)
