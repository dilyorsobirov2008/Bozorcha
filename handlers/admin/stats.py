"""
Admin statistics handler.
Aggregates key business metrics and displays them.
"""

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from locales import get_text
from keyboards.reply import admin_menu_keyboard
from states.admin_states import AdminStates
from services.stats_service import StatsService
from utils.misc import format_price

router = Router(name="admin_stats")


# ──────────────────────────────────────────────────────────
# Show statistics
# ──────────────────────────────────────────────────────────
@router.message(
    AdminStates.in_admin_menu,
    F.text.in_({"📊 Statistika", "📊 Статистика"}),
)
async def show_stats(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    today_orders = await StatsService.today_orders_count(session)
    today_sales = await StatsService.today_sales(session)
    monthly_sales = await StatsService.monthly_sales(session)
    users_count = await StatsService.users_count(session)
    top_product = await StatsService.top_product(session)

    top_name = top_product.name if top_product else "—"

    text_lines = [
        f"📊 <b>{get_text(lang, 'statistics')}</b>",
        "",
        f"📅 {get_text(lang, 'today_orders')}: {today_orders}",
        f"💵 {get_text(lang, 'today_sales')}: {format_price(today_sales or 0)}",
        f"📈 {get_text(lang, 'monthly_sales')}: {format_price(monthly_sales or 0)}",
        f"👥 {get_text(lang, 'total_users')}: {users_count}",
        f"⭐ {get_text(lang, 'top_product')}: {top_name}",
    ]

    await message.answer(
        "\n".join(text_lines),
        reply_markup=admin_menu_keyboard(lang),
    )
    # Stay in admin menu
    await state.set_state(AdminStates.in_admin_menu)
