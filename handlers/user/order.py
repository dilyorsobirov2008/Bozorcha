"""
Order / checkout handlers.
Collects address → phone → payment method, then creates the order.
"""

import logging

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from locales import get_text
from keyboards.reply import main_menu_keyboard, phone_keyboard
from keyboards.inline import payment_keyboard, order_admin_keyboard
from states.user_states import UserStates
from services.cart_service import CartService
from services.order_service import OrderService
from utils.misc import format_price
from config.settings import settings

router = Router(name="order")
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────
# Checkout  →  ask address
# ──────────────────────────────────────────────────────────
@router.callback_query(
    UserStates.in_cart,
    F.data == "checkout",
)
async def checkout_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    items = await CartService.get_items(session, callback.from_user.id)
    if not items:
        await callback.answer(get_text(lang, "cart_empty"), show_alert=True)
        return

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(get_text(lang, "send_address"))
    await state.set_state(UserStates.entering_address)
    await callback.answer()


# ──────────────────────────────────────────────────────────
# Address  →  ask phone
# ──────────────────────────────────────────────────────────
@router.message(UserStates.entering_address)
async def address_entered(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    # Support both plain text and shared location
    if message.location:
        address = f"📍 {message.location.latitude}, {message.location.longitude}"
    elif message.text:
        address = message.text.strip()
    else:
        await message.answer(get_text(lang, "invalid_address"))
        return

    await state.update_data(address=address)
    await message.answer(
        get_text(lang, "send_phone"),
        reply_markup=phone_keyboard(lang),
    )
    await state.set_state(UserStates.entering_phone)


# ──────────────────────────────────────────────────────────
# Phone  →  ask payment method
# ──────────────────────────────────────────────────────────
@router.message(UserStates.entering_phone)
async def phone_entered(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    if message.contact:
        phone = message.contact.phone_number
    elif message.text:
        phone = message.text.strip()
    else:
        await message.answer(get_text(lang, "invalid_phone"))
        return

    from services.user_service import UserService

    await UserService.update_phone(session, message.from_user.id, phone)
    await state.update_data(phone=phone)

    total = await CartService.get_total(session, message.from_user.id)
    await message.answer(
        get_text(lang, "choose_payment").format(total=format_price(total)),
        reply_markup=payment_keyboard(lang),
    )
    await state.set_state(UserStates.choosing_payment)


# ──────────────────────────────────────────────────────────
# Payment selected  →  create order
# ──────────────────────────────────────────────────────────
@router.callback_query(
    UserStates.choosing_payment,
    F.data.startswith("pay_"),
)
async def payment_selected(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    payment_type = callback.data.replace("pay_", "")  # cash / card / click / payme

    address = data.get("address", "—")
    phone = data.get("phone", "—")

    # Create order from current cart items
    order = await OrderService.create_from_cart(
        session,
        telegram_id=callback.from_user.id,
        address=address,
        phone=phone,
        payment_type=payment_type,
    )

    if not order:
        await callback.answer(get_text(lang, "order_error"), show_alert=True)
        return

    try:
        await callback.message.delete()
    except Exception:
        pass

    # Confirm to user
    await callback.message.answer(
        get_text(lang, "order_confirmed").format(order_id=order.id),
        reply_markup=main_menu_keyboard(lang),
    )

    # Notify admin group / channel
    await _notify_admins(callback.bot, order, callback.from_user, lang)

    await state.set_state(UserStates.in_main_menu)
    await callback.answer()


# ──────────────────────────────────────────────────────────
# Cancel checkout at any step
# ──────────────────────────────────────────────────────────
@router.message(
    UserStates.entering_address,
    F.text.in_({"⬅️ Ortga", "⬅️ Назад", "/cancel"}),
)
@router.message(
    UserStates.entering_phone,
    F.text.in_({"⬅️ Ortga", "⬅️ Назад", "/cancel"}),
)
async def cancel_checkout(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    await message.answer(
        get_text(lang, "order_cancelled"),
        reply_markup=main_menu_keyboard(lang),
    )
    await state.set_state(UserStates.in_main_menu)


@router.callback_query(
    UserStates.choosing_payment,
    F.data == "cancel_payment",
)
async def cancel_payment(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(
        get_text(lang, "order_cancelled"),
        reply_markup=main_menu_keyboard(lang),
    )
    await state.set_state(UserStates.in_main_menu)
    await callback.answer()


# ──────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────
async def _notify_admins(bot: Bot, order, user, lang: str):
    """Send a notification about the new order to the admin group."""
    if not settings.ADMIN_GROUP_ID:
        return

    text_lines = [
        f"🆕 <b>{get_text('uz', 'new_order')}</b>",
        f"📦 #{order.id}",
        f"👤 {user.full_name} (@{user.username or '—'})",
        f"📞 {order.phone}",
        f"📍 {order.address}",
        f"💳 {order.payment_type}",
        f"💰 {format_price(order.total)}",
    ]
    text = "\n".join(text_lines)

    try:
        await bot.send_message(
            chat_id=settings.ADMIN_GROUP_ID,
            text=text,
            reply_markup=order_admin_keyboard(order.id),
        )
    except Exception as exc:
        logger.error("Failed to notify admin group: %s", exc)
