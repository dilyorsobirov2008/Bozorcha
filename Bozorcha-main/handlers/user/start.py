"""
Start & main-menu handlers for the user-facing Telegram bot.
"""

import logging

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from keyboards.user_kb import main_menu_kb, categories_kb
from services.user import get_or_create_user
from services.category import get_categories
from states.admin_states import AdminLogin

logger = logging.getLogger(__name__)

router = Router(name="user_start")


# ──────────────────────────────────────────────
# /start
# ──────────────────────────────────────────────
@router.message(CommandStart())
async def cmd_start(message: Message, session, state: FSMContext) -> None:
    """Register (or fetch) the user and show the main menu."""
    try:
        await state.clear()

        user = await get_or_create_user(
            session=session,
            telegram_id=message.from_user.id,
            full_name=message.from_user.full_name,
            username=message.from_user.username,
        )
        logger.info(
            "User %s (%s) started the bot",
            user.full_name,
            message.from_user.id,
        )

        await message.answer(
            f"👋 Assalomu alaykum, {message.from_user.full_name}!\n\n"
            "🛒 Supermarket botimizga xush kelibsiz!\n"
            "Quyidagi menyu orqali xarid qilishingiz mumkin:",
            reply_markup=main_menu_kb(),
        )
    except Exception as e:
        logger.exception("Error in /start handler: %s", e)
        await message.answer(
            "⚠️ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring."
        )


# ──────────────────────────────────────────────
# 🛒 Harid qilish
# ──────────────────────────────────────────────
@router.message(F.text == "🛒 Harid qilish")
async def show_catalog(message: Message, session) -> None:
    """Show top-level product categories."""
    try:
        categories = await get_categories(session)

        if not categories:
            await message.answer("📭 Hozircha kategoriyalar mavjud emas.")
            return

        await message.answer(
            "📂 Kategoriyalardan birini tanlang:",
            reply_markup=categories_kb(categories),
        )
    except Exception as e:
        logger.exception("Error showing catalog: %s", e)
        await message.answer(
            "⚠️ Kategoriyalarni yuklashda xatolik yuz berdi."
        )


# ──────────────────────────────────────────────
# 🔐 Admin Panel
# ──────────────────────────────────────────────
@router.message(F.text == "🔐 Admin Panel")
async def admin_login_start(message: Message, state: FSMContext) -> None:
    """Begin the admin-login FSM: ask for username."""
    try:
        await state.set_state(AdminLogin.username)
        await message.answer(
            "🔐 Admin paneliga kirish\n\n"
            "👤 Username kiriting:",
        )
    except Exception as e:
        logger.exception("Error starting admin login: %s", e)
        await message.answer(
            "⚠️ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring."
        )
