"""
Admin main-menu handler — dispatches Inline Keyboard callback query clicks to sub-sections.
"""

import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from services.category import get_categories
from services.order import get_today_orders
from keyboards.admin_kb import (
    admin_menu_kb,
    admin_categories_kb,
    admin_products_kb,
    admin_orders_kb,
    admin_settings_kb,
    admin_select_category_kb,
)
from keyboards.user_kb import main_menu_kb

router = Router(name="admin_menu")
logger = logging.getLogger(__name__)

# ── helper: Admin Authorization ──────────────────────────────────────────
async def _is_admin(message_or_query, state: FSMContext) -> bool:
    """Return True if the user is authenticated as admin or whitelisted."""
    data = await state.get_data()
    if data.get("admin_authenticated"):
        return True

    user_id = message_or_query.from_user.id
    if user_id in settings.ADMIN_IDS:
        await state.update_data(admin_authenticated=True)
        return True

    return False

# ── 📂 Categories Handler ────────────────────────────────────────────────
@router.callback_query(F.data == "admin_categories")
async def admin_categories(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    logger.info("🎯 Triggered callback: admin_categories")
    if not await _is_admin(callback, state):
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    try:
        await state.clear()
        await state.update_data(admin_authenticated=True) # preserve auth state
        
        categories = await get_categories(session)
        if not categories:
            text = "📂 Kategoriyalar bo'sh.\nYangi kategoriya qo'shish uchun tugmani bosing."
        else:
            lines = ["📂 <b>Kategoriyalar ro'yxati:</b>\n"]
            for i, cat in enumerate(categories, 1):
                emoji = cat.emoji if cat.emoji else "📁"
                lines.append(f"{i}. {emoji} {cat.name}")
            text = "\n".join(lines)

        await callback.message.edit_text(text, reply_markup=admin_categories_kb(categories))
        await callback.answer()
    except Exception as exc:
        logger.error("admin_categories error: %s", exc, exc_info=True)
        await callback.answer("❌ Kategoriyalarni yuklashda xatolik.", show_alert=True)

# ── 📦 Products Handler ──────────────────────────────────────────────────
@router.callback_query(F.data == "admin_products")
async def admin_products(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    logger.info("🎯 Triggered callback: admin_products")
    if not await _is_admin(callback, state):
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    try:
        await state.clear()
        await state.update_data(admin_authenticated=True) # preserve auth state
        
        categories = await get_categories(session)
        await callback.message.edit_text(
            "📦 <b>Tovarlar boshqaruvi</b>\n\nKategoriya tanlang:",
            reply_markup=admin_select_category_kb(categories),
        )
        await callback.answer()
    except Exception as exc:
        logger.error("admin_products error: %s", exc, exc_info=True)
        await callback.answer("❌ Tovarlarni yuklashda xatolik.", show_alert=True)

# ── 🛒 Orders Handler ────────────────────────────────────────────────────
@router.callback_query(F.data == "admin_orders")
async def admin_orders(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    logger.info("🎯 Triggered callback: admin_orders")
    if not await _is_admin(callback, state):
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    try:
        await state.clear()
        await state.update_data(admin_authenticated=True) # preserve auth state
        
        orders = await get_today_orders(session)
        if not orders:
            text = "🛒 Bugungi buyurtmalar yo'q."
        else:
            text = f"🛒 <b>Bugungi buyurtmalar:</b> {len(orders)} ta"

        await callback.message.edit_text(text, reply_markup=admin_orders_kb(orders, page=0))
        await callback.answer()
    except Exception as exc:
        logger.error("admin_orders error: %s", exc, exc_info=True)
        await callback.answer("❌ Buyurtmalarni yuklashda xatolik.", show_alert=True)

# ── 📊 Statistics Handler ────────────────────────────────────────────────
@router.callback_query(F.data == "admin_statistics")
async def admin_statistics_menu(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    logger.info("🎯 Triggered callback: admin_statistics")
    if not await _is_admin(callback, state):
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    try:
        # Import dynamically to avoid circular references and handle in statistics router style
        from handlers.admin.statistics import show_statistics_callback
        await show_statistics_callback(callback, state, session)
    except Exception as exc:
        logger.error("admin_statistics error: %s", exc, exc_info=True)
        await callback.answer("❌ Statistikani yuklashda xatolik.", show_alert=True)

# ── ⚙️ Settings Handler ──────────────────────────────────────────────────
@router.callback_query(F.data == "admin_settings")
async def admin_settings_menu(callback: CallbackQuery, state: FSMContext) -> None:
    logger.info("🎯 Triggered callback: admin_settings")
    if not await _is_admin(callback, state):
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    try:
        await callback.message.edit_text(
            "⚙️ <b>Sozlamalar</b>\n\nKerakli bo'limni tanlang:",
            reply_markup=admin_settings_kb(),
        )
        await callback.answer()
    except Exception as exc:
        logger.error("admin_settings error: %s", exc, exc_info=True)
        await callback.answer("❌ Sozlamalarni yuklashda xatolik.", show_alert=True)

# ── 🚪 Exit Handler ──────────────────────────────────────────────────────
@router.callback_query(F.data == "admin_exit")
async def admin_logout(callback: CallbackQuery, state: FSMContext) -> None:
    logger.info("🎯 Triggered callback: admin_exit")
    if not await _is_admin(callback, state):
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    try:
        await state.clear()
        logger.info("Admin logout: tg_id=%s", callback.from_user.id)
        await callback.message.delete()
        await callback.message.answer(
            "👋 Admin panelidan chiqdingiz.",
            reply_markup=main_menu_kb(),
        )
        await callback.answer()
    except Exception as exc:
        logger.error("admin_logout error: %s", exc, exc_info=True)
        await callback.answer("❌ Xatolik yuz berdi.", show_alert=True)

# ── Callback: adm_back (back to admin main menu) ────────────────────────
@router.callback_query(F.data == "adm_back")
async def callback_admin_back(callback: CallbackQuery, state: FSMContext) -> None:
    logger.info("🎯 Triggered callback: adm_back")
    if not await _is_admin(callback, state):
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    try:
        await state.clear()
        await state.update_data(admin_authenticated=True) # preserve auth state
        await callback.message.edit_text(
            "🔑 <b>Admin panel</b>\n\nBo'limni tanlang:",
            reply_markup=admin_menu_kb(),
        )
        await callback.answer()
    except Exception as exc:
        logger.error("callback_admin_back error: %s", exc, exc_info=True)
        await callback.answer("❌ Xatolik", show_alert=True)
