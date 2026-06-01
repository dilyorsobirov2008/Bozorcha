import logging
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

from filters.admin import IsAdmin
from keyboards.admin_kb import admin_settings_kb, back_admin_kb, admin_menu_kb
from states.admin_states import SettingsState
from services.settings import (
    get_delivery_price,
    set_delivery_price,
    get_payment_toggles,
    set_payment_toggle,
)
from services.admin import get_all_admins, create_admin, delete_admin

logger = logging.getLogger(__name__)
router = Router(name="admin_settings")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

# ──────────────────────────────────────────────
# Settings main menu
# ──────────────────────────────────────────────
@router.callback_query(F.data == "adm_settings")
async def show_settings_menu(callback: CallbackQuery) -> None:
    try:
        await callback.message.edit_text(
            "⚙️ Tizim sozlamalari:\n\n"
            "Quyidagi bo'limlardan birini tanlang:",
            reply_markup=admin_settings_kb()
        )
        await callback.answer()
    except Exception as e:
        logger.exception("Error showing settings: %s", e)

# ──────────────────────────────────────────────
# Delivery price setting
# ──────────────────────────────────────────────
@router.callback_query(F.data == "adm_set_delivery")
async def edit_delivery_price_start(callback: CallbackQuery, state: FSMContext, session) -> None:
    try:
        current_price = await get_delivery_price(session)
        await state.set_state(SettingsState.value)
        await state.update_data(setting_key="delivery_price")
        
        await callback.message.edit_text(
            f"🚚 Yetkazib berish narxini sozlash\n\n"
            f"Hozirgi narx: {current_price:,.0f} so'm\n\n"
            f"✍️ Yangi narxni kiriting (faqat raqam):",
            reply_markup=back_admin_kb("adm_settings")
        )
        await callback.answer()
    except Exception as e:
        logger.exception("Error starting delivery price setting: %s", e)

@router.message(SettingsState.value)
async def edit_setting_value(message: Message, state: FSMContext, session) -> None:
    try:
        data = await state.get_data()
        key = data.get("setting_key")
        
        if key == "delivery_price":
            try:
                new_price = float(message.text.strip())
                if new_price < 0:
                    raise ValueError
            except ValueError:
                await message.answer("⚠️ Narx musbat raqam bo'lishi kerak. Qaytadan kiriting:")
                return
                
            await set_delivery_price(session, new_price)
            await message.answer(
                f"✅ Yetkazib berish narxi yangilandi: {new_price:,.0f} so'm",
                reply_markup=admin_menu_kb()
            )
            await state.clear()
            
        elif key == "add_admin_username":
            username = message.text.strip().replace("@", "")
            await state.update_data(admin_username=username)
            await state.set_state(SettingsState.select) # Wait for password
            await message.answer("✍️ Yangi admin uchun parol kiriting:")
            
    except Exception as e:
        logger.exception("Error saving setting value: %s", e)
        await message.answer("⚠️ Xatolik yuz berdi. Qaytadan urinib ko'ring.")

# ──────────────────────────────────────────────
# Payment toggles setting
# ──────────────────────────────────────────────
@router.callback_query(F.data == "adm_set_payment")
async def show_payment_toggles(callback: CallbackQuery, session) -> None:
    try:
        toggles = await get_payment_toggles(session)
        
        keyboard = []
        for ptype, enabled in toggles.items():
            status_emoji = "✅" if enabled else "❌"
            action = "disable" if enabled else "enable"
            keyboard.append([
                InlineKeyboardButton(
                    text=f"{ptype.upper()}: {status_emoji}",
                    callback_data=f"adm_pay_toggle:{ptype}:{action}"
                )
            ])
            
        keyboard.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="adm_settings")])
        
        await callback.message.edit_text(
            "💳 To'lov tizimlarini yoqish yoki o'chirish:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        await callback.answer()
    except Exception as e:
        logger.exception("Error showing payment settings: %s", e)

@router.callback_query(F.data.startswith("adm_pay_toggle:"))
async def toggle_payment_method(callback: CallbackQuery, session) -> None:
    try:
        _, ptype, action = callback.data.split(":")
        enabled = action == "enable"
        
        await set_payment_toggle(session, ptype, enabled)
        await show_payment_toggles(callback, session) # Refresh menu
        await callback.answer(f"{ptype.upper()} holati o'zgartirildi!")
    except Exception as e:
        logger.exception("Error toggling payment: %s", e)

# ──────────────────────────────────────────────
# Admins list setting
# ──────────────────────────────────────────────
@router.callback_query(F.data == "adm_set_admins")
async def show_admins_list(callback: CallbackQuery, session) -> None:
    try:
        admins = await get_all_admins(session)
        
        keyboard = []
        text = "👥 Tizim administratorlari ro'yxati:\n\n"
        
        for idx, adm in enumerate(admins, 1):
            text += f"{idx}. @{adm.username} (ID: {adm.telegram_id})\n"
            keyboard.append([
                InlineKeyboardButton(
                    text=f"🗑 @{adm.username} ni o'chirish",
                    callback_data=f"adm_del_admin:{adm.id}"
                )
            ])
            
        keyboard.append([InlineKeyboardButton(text="➕ Admin qo'shish", callback_data="adm_add_admin")])
        keyboard.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="adm_settings")])
        
        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        await callback.answer()
    except Exception as e:
        logger.exception("Error showing admin list: %s", e)

@router.callback_query(F.data == "adm_add_admin")
async def add_admin_start(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        await state.set_state(SettingsState.value)
        await state.update_data(setting_key="add_admin_username")
        await callback.message.edit_text(
            "✍️ Yangi admin telegram usernameni kiriting (masalan, admin_username):",
            reply_markup=back_admin_kb("adm_set_admins")
        )
        await callback.answer()
    except Exception as e:
        logger.exception("Error starting admin creation: %s", e)

@router.message(SettingsState.select) # Input password state
async def add_admin_password(message: Message, state: FSMContext, session) -> None:
    try:
        data = await state.get_data()
        username = data.get("admin_username")
        password = message.text.strip()
        
        # In a real app we might ask for telegram_id, let's auto default to 0 for username logins
        # Since Telegram bot auth doesn't strictly need telegram_id if they log in via web panel,
        # but in this bot admin panel has FSM username/password.
        new_adm = await create_admin(
            session=session,
            telegram_id=0, # Username login authentication doesn't require a real telegram ID
            username=username,
            password=password
        )
        
        await message.answer(
            f"✅ Yangi administrator @{new_adm.username} yaratildi!",
            reply_markup=admin_menu_kb()
        )
        await state.clear()
    except Exception as e:
        logger.exception("Error finishing admin creation: %s", e)
        await message.answer("⚠️ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")

@router.callback_query(F.data.startswith("adm_del_admin:"))
async def delete_admin_click(callback: CallbackQuery, session) -> None:
    try:
        admin_id = int(callback.data.split(":")[1])
        success = await delete_admin(session, admin_id)
        
        if success:
            await callback.answer("Admin muvaffaqiyatli o'chirildi.")
        else:
            await callback.answer("⚠️ Adminni o'chirib bo'lmadi.", show_alert=True)
            
        await show_admins_list(callback, session) # Refresh
    except Exception as e:
        logger.exception("Error deleting admin: %s", e)
