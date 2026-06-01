"""Admin login handler — username/password authentication via FSM."""

import logging

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from config.settings import settings
from services.admin import authenticate_admin
from keyboards.admin_kb import admin_menu_kb
from keyboards.user_kb import main_menu_kb
from states.admin_states import AdminLogin

router = Router(name='admin_login')
logger = logging.getLogger(__name__)


# ── Trigger: /admin command ─────────────────────────────────────────────
@router.message(F.text == '/admin')
async def cmd_admin(message: Message, state: FSMContext) -> None:
    """Start admin login flow or go straight to menu if already authed."""
    try:
        data = await state.get_data()

        # Already authenticated via FSM
        if data.get('admin_authenticated'):
            await message.answer(
                '🔑 Siz allaqachon admin panelidasiz.',
                reply_markup=admin_menu_kb(),
            )
            return

        # Pre-authorised by Telegram ID
        if message.from_user.id in settings.ADMIN_IDS:
            await state.update_data(admin_authenticated=True)
            await message.answer(
                '👋 Xush kelibsiz, admin!',
                reply_markup=admin_menu_kb(),
            )
            return

        # Ask for credentials
        await state.set_state(AdminLogin.username)
        await message.answer(
            '🔐 Admin paneliga kirish\n\n'
            '👤 Foydalanuvchi nomingizni kiriting:',
        )
    except Exception as exc:
        logger.error('cmd_admin error: %s', exc, exc_info=True)
        await message.answer('❌ Xatolik yuz berdi. Qayta urinib ko\'ring.')


# ── State: username ─────────────────────────────────────────────────────
@router.message(AdminLogin.username)
async def process_username(message: Message, state: FSMContext) -> None:
    """Save the entered username and ask for password."""
    try:
        username = message.text.strip()
        if not username:
            await message.answer('❌ Foydalanuvchi nomi bo\'sh bo\'lishi mumkin emas. Qayta kiriting:')
            return

        await state.update_data(username=username)
        await state.set_state(AdminLogin.password)
        await message.answer('🔒 Parolingizni kiriting:')
    except Exception as exc:
        logger.error('process_username error: %s', exc, exc_info=True)
        await state.clear()
        await message.answer('❌ Xatolik yuz berdi. /admin buyrug\'ini qayta yuboring.')


# ── State: password ─────────────────────────────────────────────────────
@router.message(AdminLogin.password)
async def process_password(message: Message, session, state: FSMContext) -> None:
    """Verify credentials and grant access or reject."""
    try:
        data = await state.get_data()
        username = data.get('username', '')
        password = message.text.strip()

        # Try to delete the password message for security
        try:
            await message.delete()
        except Exception:
            pass

        if not password:
            await message.answer('❌ Parol bo\'sh bo\'lishi mumkin emas. Qayta kiriting:')
            return

        admin = await authenticate_admin(session, username, password)

        if admin:
            await state.clear()
            await state.update_data(admin_authenticated=True, admin_id=admin.id)
            logger.info(
                'Admin login success: user=%s tg_id=%s',
                username,
                message.from_user.id,
            )
            await message.answer(
                f'✅ Muvaffaqiyatli kirdingiz!\n\n'
                f'👋 Xush kelibsiz, <b>{admin.username}</b>!',
                reply_markup=admin_menu_kb(),
            )
        else:
            logger.warning(
                'Admin login failed: user=%s tg_id=%s',
                username,
                message.from_user.id,
            )
            await state.clear()
            await message.answer(
                '❌ Login yoki parol noto\'g\'ri!\n\n'
                'Qayta urinish uchun /admin buyrug\'ini yuboring.',
                reply_markup=main_menu_kb(),
            )
    except Exception as exc:
        logger.error('process_password error: %s', exc, exc_info=True)
        await state.clear()
        await message.answer(
            '❌ Xatolik yuz berdi. /admin buyrug\'ini qayta yuboring.',
            reply_markup=main_menu_kb(),
        )
