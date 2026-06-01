from typing import Any

from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from services.admin import is_admin as is_admin_in_db


class IsAdmin(Filter):
    """Filter that checks if the user is an admin.

    Checks two sources:
    1. Config-level ADMIN_IDS list (from settings)
    2. Database admin table (via services.admin.is_admin)

    Passes if the user's telegram_id is found in either source.
    """

    async def __call__(
        self,
        event: Message | CallbackQuery,
        session: AsyncSession | None = None,
        **kwargs: Any,
    ) -> bool:
        if isinstance(event, CallbackQuery):
            user = event.from_user
        else:
            user = event.from_user

        if user is None:
            return False

        telegram_id = user.id

        # Check config-level admin list first (fast path)
        if telegram_id in settings.ADMIN_IDS:
            return True

        # Check database if session is available
        if session is not None:
            return await is_admin_in_db(session, telegram_id)

        return False
