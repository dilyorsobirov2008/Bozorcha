import asyncio
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from locales import get_text
from keyboards.reply import admin_settings_keyboard
from states.admin_states import AdminStates
from services.user_service import UserService

router = Router(name="admin_broadcast")


@router.message(
    AdminStates.in_admin_menu,
    F.text.in_({"📢 Reklama yuborish", "📢 Рассылка"}),
)
async def broadcast_start(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    await message.answer(get_text(lang, "broadcast_enter"))
    await state.set_state(AdminStates.entering_broadcast)


@router.message(AdminStates.entering_broadcast)
async def broadcast_message_process(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    # If user cancels
    if message.text in {"⬅️ Ortga", "⬅️ Назад", "/cancel"}:
        await message.answer(
            get_text(lang, "admin_settings"),
            reply_markup=admin_settings_keyboard(lang),
        )
        await state.set_state(AdminStates.in_admin_menu)
        return

    # Get all users to send to
    user_ids = await UserService.get_all_ids(session)
    if not user_ids:
        await message.answer(
            "❌ Foydalanuvchilar mavjud emas!\nНет пользователей!",
            reply_markup=admin_settings_keyboard(lang),
        )
        await state.set_state(AdminStates.in_admin_menu)
        return

    progress_msg = await message.answer("🔄 Reklama yuborilmoqda... / Рассылка отправляется...")
    success_count = 0

    for user_id in user_ids:
        try:
            # copy_to maintains formatting, entities, photos, videos, etc.
            await message.copy_to(chat_id=user_id)
            success_count += 1
            # Rate limiting / anti-flood check
            await asyncio.sleep(0.05)
        except Exception as e:
            logging.warning(f"Failed to send broadcast to {user_id}: {e}")

    try:
        await progress_msg.delete()
    except Exception:
        pass

    await message.answer(
        get_text(lang, "broadcast_sent", count=success_count),
        reply_markup=admin_settings_keyboard(lang),
    )
    await state.set_state(AdminStates.in_admin_menu)
