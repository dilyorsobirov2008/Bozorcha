"""Admin order management — view details, update status, paginate, notify user."""

import logging

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from services.order import get_order, update_order_status, get_today_orders
from keyboards.admin_kb import order_status_kb, admin_orders_kb, back_admin_kb
from utils.helpers import format_price, format_order_status, format_payment_type

router = Router(name="admin_orders")
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

def _order_detail_text(order) -> str:
    """Build the full order detail message."""
    # Items list
    items_lines = []
    for item in order.items:
        product_name = item.product.name if hasattr(item, "product") and item.product else f"#{item.product_id}"
        items_lines.append(
            f"  • {product_name} × {item.quantity} = {format_price(item.price * item.quantity)}"
        )
    items_text = "\n".join(items_lines) if items_lines else "  (bo'sh)"

    user_name = "—"
    if hasattr(order, "user") and order.user:
        user_name = order.user.full_name or order.user.username or str(order.user.telegram_id)

    created_at = order.created_at.strftime("%d.%m.%Y %H:%M") if order.created_at else "—"
    phone = getattr(order, "phone", "—") or "—"
    address = getattr(order, "address", "—") or "—"

    return (
        f"📋 <b>Buyurtma #{order.id}</b>\n"
        f"📅 Sana: {created_at}\n"
        f"👤 Mijoz: {user_name}\n"
        f"📞 Tel: {phone}\n"
        f"📍 Manzil: {address}\n"
        f"💳 To'lov: {format_payment_type(order.payment_type)}\n"
        f"📊 Status: {format_order_status(order.status)}\n\n"
        f"📦 <b>Mahsulotlar:</b>\n{items_text}\n\n"
        f"💰 <b>Jami: {format_price(order.total)}</b>"
    )

# ── View order ───────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("adm_ord_view:"))
async def cb_view_order(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    logger.info("🎯 Triggered callback: adm_ord_view")
    if not await _is_admin(callback, state):
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    try:
        order_id = int(callback.data.split(":")[1])
        order = await get_order(session, order_id)
        if not order:
            await callback.answer("❌ Buyurtma topilmadi", show_alert=True)
            return

        text = _order_detail_text(order)
        await callback.message.edit_text(
            text,
            reply_markup=order_status_kb(order.id),
        )
        await callback.answer()
    except Exception as exc:
        logger.error("cb_view_order error: %s", exc, exc_info=True)
        await callback.answer("❌ Xatolik", show_alert=True)

# ── Update order status ─────────────────────────────────────────────────
@router.callback_query(F.data.startswith("adm_ord_status:"))
async def cb_update_order_status(callback: CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession) -> None:
    logger.info("🎯 Triggered callback: adm_ord_status")
    if not await _is_admin(callback, state):
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    try:
        parts = callback.data.split(":")
        order_id = int(parts[1])
        new_status = parts[2]

        order = await update_order_status(session, order_id, new_status)
        if not order:
            await callback.answer("❌ Buyurtma topilmadi", show_alert=True)
            return

        logger.info("Order status updated: id=%s status=%s", order_id, new_status)

        # Update admin message
        text = _order_detail_text(order)
        await callback.message.edit_text(
            text,
            reply_markup=order_status_kb(order.id),
        )
        await callback.answer(f"✅ Status: {format_order_status(order.status)}")

        # Notify the user about the status change
        try:
            user_tg_id = None
            if hasattr(order, "user") and order.user:
                user_tg_id = order.user.telegram_id

            if user_tg_id:
                status_emoji = {
                    "new": "🆕",
                    "accepted": "✅",
                    "delivering": "🚚",
                    "completed": "🏁",
                    "canceled": "❌",
                }
                emoji = status_emoji.get(new_status, "📋")

                await bot.send_message(
                    chat_id=user_tg_id,
                    text=(
                        f"{emoji} <b>Buyurtmangiz statusi o'zgartirildi!</b>\n\n"
                        f"📊 Yangi status: {format_order_status(order.status)}\n\n"
                        f"💰 Jami: {format_price(order.total)}"
                    ),
                )
                logger.info("User notified about order status: tg_id=%s order=%s", user_tg_id, order_id)
        except Exception as notify_exc:
            logger.warning("Failed to notify user about order status: %s", notify_exc)

    except Exception as exc:
        logger.error("cb_update_order_status error: %s", exc, exc_info=True)
        await callback.answer("❌ Xatolik", show_alert=True)

# ── Paginate orders ─────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("adm_ord_page:"))
async def cb_orders_page(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    logger.info("🎯 Triggered callback: adm_ord_page")
    if not await _is_admin(callback, state):
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    try:
        page = int(callback.data.split(":")[1])
        orders = await get_today_orders(session)

        if not orders:
            text = "🛒 Buyurtmalar yo'q."
        else:
            text = f"🛒 <b>Buyurtmalar:</b> {len(orders)} ta"

        await callback.message.edit_text(
            text,
            reply_markup=admin_orders_kb(orders, page=page),
        )
        await callback.answer()
    except Exception as exc:
        logger.error("cb_orders_page error: %s", exc, exc_info=True)
        await callback.answer("❌ Xatolik", show_alert=True)

# ── Back to orders ───────────────────────────────────────────────────────
@router.callback_query(F.data == "adm_back_orders")
async def cb_back_to_orders(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    logger.info("🎯 Triggered callback: adm_back_orders")
    if not await _is_admin(callback, state):
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    try:
        orders = await get_today_orders(session)
        if not orders:
            text = "🛒 Bugungi buyurtmalar yo'q."
        else:
            text = f"🛒 <b>Bugungi buyurtmalar:</b> {len(orders)} ta"

        await callback.message.edit_text(
            text,
            reply_markup=admin_orders_kb(orders, page=0),
        )
        await callback.answer()
    except Exception as exc:
        logger.error("cb_back_to_orders error: %s", exc, exc_info=True)
        await callback.answer("❌ Xatolik", show_alert=True)
