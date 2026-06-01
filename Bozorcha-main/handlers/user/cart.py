"""
Shopping-cart handlers – view cart, update quantities, remove items, clear.
"""

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from keyboards.user_kb import cart_kb
from services.cart import (
    clear_cart,
    get_cart,
    get_cart_item,
    get_cart_total,
    remove_from_cart,
    update_cart_quantity,
)
from utils.helpers import format_price

logger = logging.getLogger(__name__)

router = Router(name="user_cart")


# ──────────────────────────────────────────────
# helpers
# ──────────────────────────────────────────────
def _empty_cart_kb() -> InlineKeyboardMarkup:
    """Inline keyboard shown when the cart is empty."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 Bosh menyu",
                    callback_data="back_to_menu",
                )
            ]
        ]
    )


async def _render_cart(
    callback_or_message,
    session,
    user_id: int,
    *,
    edit: bool = False,
) -> None:
    """Build the cart text + keyboard and send/edit the message."""
    cart_items = await get_cart(session, user_id)

    if not cart_items:
        text = "🛒 Savatcha bo'sh"
        kb = _empty_cart_kb()
    else:
        total = await get_cart_total(session, user_id)
        lines: list[str] = ["🛒 Sizning savatchangiz:\n"]
        for item in cart_items:
            item_total = item.quantity * item.product.price
            lines.append(
                f"  {item.product.name} x {item.quantity} = "
                f"{format_price(item_total)}"
            )
        lines.append(f"\n💰 Jami: {format_price(total)}")
        text = "\n".join(lines)
        kb = cart_kb(cart_items)

    if edit:
        # Editing an existing inline message
        msg = (
            callback_or_message.message
            if isinstance(callback_or_message, CallbackQuery)
            else callback_or_message
        )
        try:
            await msg.edit_text(text, reply_markup=kb)
        except Exception:
            # If the message content didn't change, Telegram raises an error
            pass
    else:
        target = (
            callback_or_message.message
            if isinstance(callback_or_message, CallbackQuery)
            else callback_or_message
        )
        await target.answer(text, reply_markup=kb)


# ──────────────────────────────────────────────
# Show cart – text button or inline callback
# ──────────────────────────────────────────────
@router.message(F.text == "🛒 Savatcha")
async def show_cart_text(message: Message, session) -> None:
    """Show cart via reply-keyboard button."""
    try:
        await _render_cart(message, session, message.from_user.id)
    except Exception as e:
        logger.exception("Error showing cart: %s", e)
        await message.answer("⚠️ Savatchani yuklashda xatolik yuz berdi.")


@router.callback_query(F.data == "back_to_cart")
async def show_cart_callback(callback: CallbackQuery, session) -> None:
    """Show cart via inline callback (back navigation)."""
    try:
        await callback.answer()
        await _render_cart(
            callback, session, callback.from_user.id, edit=True
        )
    except Exception as e:
        logger.exception("Error showing cart via callback: %s", e)
        await callback.answer("⚠️ Xatolik yuz berdi", show_alert=True)


# ──────────────────────────────────────────────
# Cart quantity +/-
# ──────────────────────────────────────────────
@router.callback_query(F.data.regexp(r"^cart_qty:\d+:plus$"))
async def cart_qty_plus(callback: CallbackQuery, session) -> None:
    """Increment quantity for a cart item."""
    try:
        item_id = int(callback.data.split(":")[1])
        cart_item = await get_cart_item(session, item_id)

        if not cart_item:
            await callback.answer("❌ Element topilmadi", show_alert=True)
            return

        if cart_item.quantity >= cart_item.product.stock:
            await callback.answer(
                f"📦 Omborda faqat {cart_item.product.stock} dona mavjud",
                show_alert=True,
            )
            return

        await update_cart_quantity(
            session, item_id, cart_item.quantity + 1
        )
        await callback.answer()
        await _render_cart(
            callback, session, callback.from_user.id, edit=True
        )
    except Exception as e:
        logger.exception("Error cart_qty_plus: %s", e)
        await callback.answer("⚠️ Xatolik yuz berdi", show_alert=True)


@router.callback_query(F.data.regexp(r"^cart_qty:\d+:minus$"))
async def cart_qty_minus(callback: CallbackQuery, session) -> None:
    """Decrement cart-item quantity; remove if it reaches 0."""
    try:
        item_id = int(callback.data.split(":")[1])
        cart_item = await get_cart_item(session, item_id)

        if not cart_item:
            await callback.answer("❌ Element topilmadi", show_alert=True)
            return

        new_qty = cart_item.quantity - 1
        if new_qty <= 0:
            await remove_from_cart(session, item_id)
        else:
            await update_cart_quantity(session, item_id, new_qty)

        await callback.answer()
        await _render_cart(
            callback, session, callback.from_user.id, edit=True
        )
    except Exception as e:
        logger.exception("Error cart_qty_minus: %s", e)
        await callback.answer("⚠️ Xatolik yuz berdi", show_alert=True)


# ──────────────────────────────────────────────
# Remove a single item
# ──────────────────────────────────────────────
@router.callback_query(F.data.startswith("cart_del:"))
async def cart_delete_item(callback: CallbackQuery, session) -> None:
    """Remove an item from the cart entirely."""
    try:
        item_id = int(callback.data.split(":")[1])
        cart_item = await get_cart_item(session, item_id)

        if not cart_item:
            await callback.answer("❌ Element topilmadi", show_alert=True)
            return

        product_name = cart_item.product.name
        await remove_from_cart(session, item_id)

        await callback.answer(f"🗑 {product_name} o'chirildi")
        await _render_cart(
            callback, session, callback.from_user.id, edit=True
        )
    except Exception as e:
        logger.exception("Error deleting cart item: %s", e)
        await callback.answer("⚠️ Xatolik yuz berdi", show_alert=True)


# ──────────────────────────────────────────────
# Clear the whole cart
# ──────────────────────────────────────────────
@router.callback_query(F.data == "cart_clear")
async def cart_clear_all(callback: CallbackQuery, session) -> None:
    """Remove every item from the cart."""
    try:
        await clear_cart(session, callback.from_user.id)
        await callback.answer("🗑 Savatcha tozalandi")
        await _render_cart(
            callback, session, callback.from_user.id, edit=True
        )
    except Exception as e:
        logger.exception("Error clearing cart: %s", e)
        await callback.answer("⚠️ Xatolik yuz berdi", show_alert=True)
