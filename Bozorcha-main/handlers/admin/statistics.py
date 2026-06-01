"""Admin statistics dashboard — today, monthly, total, best-selling."""

import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from services.order import get_today_stats, get_monthly_stats, get_total_sales, get_best_selling
from services.user import count_users
from services.product import count_products
from keyboards.admin_kb import back_admin_kb
from utils.helpers import format_price

router = Router(name="admin_statistics")
logger = logging.getLogger(__name__)

async def _is_admin(event, state: FSMContext) -> bool:
    data = await state.get_data()
    if data.get("admin_authenticated"):
        return True
    user_id = event.from_user.id if hasattr(event, "from_user") else None
    if user_id and user_id in settings.ADMIN_IDS:
        await state.update_data(admin_authenticated=True)
        return True
    return False

async def show_statistics_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    """Helper to build stats and edit the message text."""
    try:
        # Gather all data asynchronously with DB session
        today = await get_today_stats(session)
        monthly = await get_monthly_stats(session)
        total = await get_total_sales(session)
        users_count = await count_users(session)
        products_count = await count_products(session)
        best = await get_best_selling(session)

        # Parse today stats
        today_count = today.get("count", 0) if isinstance(today, dict) else 0
        today_sum = today.get("sum", 0) if isinstance(today, dict) else 0

        # Parse monthly stats
        monthly_count = monthly.get("count", 0) if isinstance(monthly, dict) else 0
        monthly_sum = monthly.get("sum", 0) if isinstance(monthly, dict) else 0

        # Parse total stats
        total_count = total.get("count", 0) if isinstance(total, dict) else 0
        total_sum = total.get("sum", 0) if isinstance(total, dict) else 0

        # Parse best sellers
        best_lines = []
        if best:
            for i, item in enumerate(best[:10], 1):
                name = item.get("name", "—") if isinstance(item, dict) else getattr(item, "name", "—")
                qty = item.get("total_sold", 0) if isinstance(item, dict) else getattr(item, "total_sold", 0)
                best_lines.append(f"  {i}. {name} — {qty} ta")
        best_text = "\n".join(best_lines) if best_lines else "  Ma'lumot yo'q"

        text = (
            "📊 <b>Statistika</b>\n\n"
            "📅 <b>Bugun:</b>\n"
            f"  Buyurtmalar: {today_count}\n"
            f"  Savdo: {format_price(today_sum)}\n\n"
            "📆 <b>Oylik:</b>\n"
            f"  Buyurtmalar: {monthly_count}\n"
            f"  Savdo: {format_price(monthly_sum)}\n\n"
            "📈 <b>Umumiy:</b>\n"
            f"  Buyurtmalar: {total_count}\n"
            f"  Savdo: {format_price(total_sum)}\n"
            f"  Foydalanuvchilar: {users_count}\n"
            f"  Tovarlar: {products_count}\n\n"
            f"🏆 <b>Eng ko'p sotilgan:</b>\n{best_text}"
        )

        await callback.message.edit_text(text, reply_markup=back_admin_kb())
        await callback.answer()
    except Exception as exc:
        logger.error("show_statistics_callback error: %s", exc, exc_info=True)
        await callback.answer("❌ Statistikani yuklashda xatolik.", show_alert=True)

@router.callback_query(F.data.in_({"admin_statistics", "adm_statistics"}))
async def cb_statistics(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    logger.info("🎯 Triggered callback: admin_statistics / adm_statistics")
    if not await _is_admin(callback, state):
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    await show_statistics_callback(callback, state, session)
