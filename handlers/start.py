"""
Start & language-selection handlers.
"""

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from locales import get_text
from keyboards.reply import language_keyboard, main_menu_keyboard
from states.user_states import UserStates
from services.user_service import UserService

router = Router(name="start")


# ──────────────────────────────────────────────────────────
# /start command
# ──────────────────────────────────────────────────────────
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, session: AsyncSession):
    """Greet the user and ask them to pick a language."""
    await state.clear()
    await message.answer(
        "Tilni tanlang / Выберите язык:",
        reply_markup=language_keyboard(),
    )
    await state.set_state(UserStates.choosing_language)


# ──────────────────────────────────────────────────────────
# Language selection
# ──────────────────────────────────────────────────────────
@router.message(
    UserStates.choosing_language,
    F.text.in_({"🇺🇿 O'zbekcha", "🇷🇺 Русский"}),
)
async def language_chosen(message: Message, state: FSMContext, session: AsyncSession):
    """Persist the selected language and show the main menu."""
    lang = "uz" if message.text == "🇺🇿 O'zbekcha" else "ru"

    # Upsert user record
    user = await UserService.get_or_create(
        session,
        telegram_id=message.from_user.id,
        full_name=message.from_user.full_name,
    )
    await UserService.update_language(session, message.from_user.id, lang)

    # Store language in FSM so every handler can access it quickly
    await state.update_data(lang=lang, user_id=user.id)

    await message.answer(
        get_text(lang, "welcome"),
        reply_markup=main_menu_keyboard(lang),
    )
    await state.set_state(UserStates.in_main_menu)
