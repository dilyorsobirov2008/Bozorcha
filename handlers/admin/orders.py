"""
Admin order management handlers.
View / filter orders by status, accept, ship, cancel.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from locales import get_text
from keyboards.reply import admin_menu_keyboard, admin_orders_keyboard
from keyboards.inline import (
    order_list_inline_keyboard,
    order_admin_keyboard,
    pagination_keyboard,
)
from states.admin_states import AdminStates
from services.order_service import OrderService
from utils.pagination import Paginator
from utils.misc import format_price

router = Router(name="admin_orders")

ORDERS_PER_PAGE = 6

# Status label → DB enum mapping
_STATUS_MAP_UZ = {
    "🆕 Yangi": "new",
    "🚚 Yetkazilmoqda": "delivering",
    "✅ Bajarilgan": "completed",
    "❌ Bekor qilingan": "cancelled",
}
_STATUS_MAP_RU = {
    "🆕 Новые": "new",
    "🚚 Доставка": "delivering",
    "✅ Завершённые": "completed",
    "❌ Отменённые": "cancelled",
}


# ──────────────────────────────────────────────────────────
# Orders menu
# ──────────────────────────────────────────────────────────
@router.message(
    AdminStates.in_admin_menu,
    F.text.in_({"📋 Buyurtmalar", "📋 Заказы"}),
)
async def orders_menu(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    # Show counts per status
    new_count = await OrderService.count_by_status(session, "new")
    delivering_count = await OrderService.count_by_status(session, "delivering")
    completed_count = await OrderService.count_by_status(session, "completed")
    cancelled_count = await OrderService.count_by_status(session, "cancelled")

    text = get_text(lang, "admin_orders_menu").format(
        new=new_count,
        delivering=delivering_count,
        completed=completed_count,
        cancelled=cancelled_count,
    )

    await message.answer(text, reply_markup=admin_orders_keyboard(lang))
    await state.set_state(AdminStates.in_orders_menu)


# ──────────────────────────────────────────────────────────
# Filter by status
# ──────────────────────────────────────────────────────────
@router.message(AdminStates.in_orders_menu, F.text)
async def filter_orders_by_status(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    status_map = _STATUS_MAP_UZ if lang == "uz" else _STATUS_MAP_RU
    status = status_map.get(message.text)

    if message.text in {"⬅️ Ortga", "⬅️ Назад"}:
        await message.answer(
            get_text(lang, "admin_menu"),
            reply_markup=admin_menu_keyboard(lang),
        )
        await state.set_state(AdminStates.in_admin_menu)
        return

    if not status:
        return  # Ignore unknown text

    await state.update_data(order_status=status, order_page=1)
    await _show_orders_page(message, state, session, status, page=1, lang=lang)


async def _show_orders_page(target, state, session, status, page, lang):
    total = await OrderService.count_by_status(session, status)
    offset = (page - 1) * ORDERS_PER_PAGE
    orders = await OrderService.get_by_status(
        session, status, offset=offset, limit=ORDERS_PER_PAGE
    )
    paginator = Paginator(total=total, per_page=ORDERS_PER_PAGE, current_page=page)

    if not orders:
        if isinstance(target, Message):
            await target.answer(get_text(lang, "no_orders"))
        else:
            await target.message.edit_text(get_text(lang, "no_orders"))
        return

    text = get_text(lang, "orders_list_title").format(status=status, total=total)
    if paginator.total_pages > 1:
        text += f"\n📄 {page}/{paginator.total_pages}"

    markup = order_list_inline_keyboard(orders, lang)

    if isinstance(target, Message):
        await target.answer(text, reply_markup=markup)
    else:
        await target.message.edit_text(text, reply_markup=markup)


# ──────────────────────────────────────────────────────────
# Pagination
# ──────────────────────────────────────────────────────────
@router.callback_query(
    AdminStates.in_orders_menu,
    F.data.in_({"ord_page_next", "ord_page_prev"}),
)
async def paginate_orders(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    status = data.get("order_status", "new")
    page = data.get("order_page", 1)

    page = page + 1 if callback.data == "ord_page_next" else max(1, page - 1)
    await state.update_data(order_page=page)
    await _show_orders_page(callback, state, session, status, page, lang)
    await callback.answer()


# ──────────────────────────────────────────────────────────
# View single order
# ──────────────────────────────────────────────────────────
@router.callback_query(
    AdminStates.in_orders_menu,
    F.data.startswith("view_order_"),
)
async def view_order(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    order_id = int(callback.data.split("_")[-1])

    order = await OrderService.get_by_id(session, order_id)
    if not order:
        await callback.answer(get_text(lang, "order_not_found"), show_alert=True)
        return

    text = _format_order_detail(order, lang)
    markup = order_admin_keyboard(order_id)

    await callback.message.edit_text(text, reply_markup=markup)
    await callback.answer()


# ──────────────────────────────────────────────────────────
# Accept / Ship / Cancel
# ──────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("accept_"))
async def accept_order(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    order_id = int(callback.data.split("_")[-1])

    await OrderService.update_status(session, order_id, "accepted")
    await callback.answer(get_text(lang, "order_accepted"), show_alert=True)

    order = await OrderService.get_by_id(session, order_id)
    text = _format_order_detail(order, lang)
    markup = order_admin_keyboard(order_id)
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except Exception:
        pass


@router.callback_query(F.data.startswith("ship_"))
async def ship_order(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    order_id = int(callback.data.split("_")[-1])

    await OrderService.update_status(session, order_id, "delivering")
    await callback.answer(get_text(lang, "order_shipped"), show_alert=True)

    order = await OrderService.get_by_id(session, order_id)
    text = _format_order_detail(order, lang)
    markup = order_admin_keyboard(order_id)
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except Exception:
        pass


@router.callback_query(F.data.startswith("cancel_order_"))
async def cancel_order(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    order_id = int(callback.data.split("_")[-1])

    await OrderService.update_status(session, order_id, "cancelled")
    await callback.answer(get_text(lang, "order_cancelled_admin"), show_alert=True)

    order = await OrderService.get_by_id(session, order_id)
    text = _format_order_detail(order, lang)
    markup = order_admin_keyboard(order_id)
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except Exception:
        pass


# ──────────────────────────────────────────────────────────
# Back to admin menu
# ──────────────────────────────────────────────────────────
@router.callback_query(
    AdminStates.in_orders_menu,
    F.data == "back_to_admin",
)
async def back_from_orders(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        get_text(lang, "admin_menu"),
        reply_markup=admin_menu_keyboard(lang),
    )
    await state.set_state(AdminStates.in_admin_menu)
    await callback.answer()


# ──────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────
def _format_order_detail(order, lang: str) -> str:
    status_icons = {
        "new": "🆕",
        "accepted": "✅",
        "delivering": "🚚",
        "completed": "🏁",
        "cancelled": "❌",
    }
    icon = status_icons.get(order.status, "📦")
    lines = [
        f"{icon} <b>{get_text(lang, 'order')} #{order.id}</b>",
        "",
        f"👤 {get_text(lang, 'customer')}: {order.user.full_name if hasattr(order, 'user') and order.user else '—'}",
        f"📞 {get_text(lang, 'phone')}: {order.phone or '—'}",
        f"📍 {get_text(lang, 'address')}: {order.address or '—'}",
        f"💳 {get_text(lang, 'payment')}: {order.payment_type or '—'}",
        f"📊 {get_text(lang, 'status')}: {order.status}",
        f"💰 {get_text(lang, 'total')}: {format_price(order.total)}",
    ]

    # Order items
    if hasattr(order, "items") and order.items:
        lines.append("")
        lines.append(f"📝 <b>{get_text(lang, 'order_items')}:</b>")
        for idx, item in enumerate(order.items, 1):
            product_name = item.product.name if hasattr(item, "product") and item.product else f"#{item.product_id}"
            lines.append(
                f"  {idx}. {product_name} x{item.quantity} — {format_price(item.price * item.quantity)}"
            )

    return "\n".join(lines)
