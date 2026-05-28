"""
Admin authentication handlers.
Login / password flow and logout.
"""

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from locales import get_text
from keyboards.reply import main_menu_keyboard, admin_menu_keyboard
from states.user_states import UserStates
from states.admin_states import AdminStates
from services.admin_service import AdminService

router = Router(name="admin_auth")


# ──────────────────────────────────────────────────────────
# Admin Panel button  →  ask login
# ──────────────────────────────────────────────────────────
@router.message(
    UserStates.in_main_menu,
    F.text.in_({"🔐 Admin Panel", "🔐 Админ панель"}),
)
async def admin_panel_entry(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    await message.answer(get_text(lang, "admin_login"))
    await state.set_state(AdminStates.entering_login)


# ──────────────────────────────────────────────────────────
# Login  →  ask password
# ──────────────────────────────────────────────────────────
@router.message(AdminStates.entering_login)
async def admin_login_entered(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    await state.update_data(admin_login=message.text.strip())
    await message.answer(get_text(lang, "admin_password"))
    await state.set_state(AdminStates.entering_password)


# ──────────────────────────────────────────────────────────
# Password  →  authenticate
# ──────────────────────────────────────────────────────────
@router.message(AdminStates.entering_password)
async def admin_password_entered(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    login = data.get("admin_login", "")
    password = message.text.strip()

    # Try to delete the password message for security
    try:
        await message.delete()
    except Exception:
        pass

    admin = await AdminService.authenticate(session, login, password)
    if admin:
        await state.update_data(admin_id=admin.id)
        await message.answer(
            get_text(lang, "admin_welcome"),
            reply_markup=admin_menu_keyboard(lang),
        )
        await state.set_state(AdminStates.in_admin_menu)
    else:
        await message.answer(
            get_text(lang, "wrong_credentials"),
            reply_markup=main_menu_keyboard(lang),
        )
        await state.set_state(UserStates.in_main_menu)


# ──────────────────────────────────────────────────────────
# Logout (from any admin state)
# ──────────────────────────────────────────────────────────
@router.message(
    AdminStates.in_admin_menu,
    F.text.in_({"🚪 Chiqish", "🚪 Выход"}),
)
async def admin_logout(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    # Keep lang but clear admin data
    await state.clear()
    await state.update_data(lang=lang)

    await message.answer(
        get_text(lang, "logged_out"),
        reply_markup=main_menu_keyboard(lang),
    )
    await state.set_state(UserStates.in_main_menu)


# Cancel / back from login flow
@router.message(
    AdminStates.entering_login,
    F.text.in_({"⬅️ Ortga", "⬅️ Назад", "/cancel"}),
)
@router.message(
    AdminStates.entering_password,
    F.text.in_({"⬅️ Ortga", "⬅️ Назад", "/cancel"}),
)
async def cancel_admin_login(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    await message.answer(
        get_text(lang, "main_menu"),
        reply_markup=main_menu_keyboard(lang),
    )
    await state.set_state(UserStates.in_main_menu)
