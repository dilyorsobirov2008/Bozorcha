import time
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message

class ThrottleMiddleware(BaseMiddleware):
    """Simple anti-flood throttle middleware using message timestamps."""
    def __init__(self, limit: float = 0.5):
        self.limit = limit
        self.last_msg_time = {}
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        # Only throttle messages
        if not isinstance(event, Message) or not event.from_user:
            return await handler(event, data)

        user_id = event.from_user.id
        now = time.time()
        
        if user_id in self.last_msg_time:
            delta = now - self.last_msg_time[user_id]
            if delta < self.limit:
                # Silently ignore messages sent too quickly
                return

        self.last_msg_time[user_id] = now
        return await handler(event, data)
