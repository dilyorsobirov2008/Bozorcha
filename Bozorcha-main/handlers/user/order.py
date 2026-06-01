"""
Order-flow handlers – checkout → address → phone → payment → confirm/cancel.
Sends an order notification to the admin group on confirmation.
"""

import logging
import re

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config.settings import settings
from keyboards.admin_kb import order_status_kb
from keyboards.user_kb import (
    confirm_order_kb,
    main_menu_kb,
    payment_kb,
    phone_kb,
)
from models.order import PaymentType
from services.cart import get_cart, get_cart_total
from services.order import create_order_from_cart
from services.settings import get_delivery_price, get_payment_toggles
from services.user import get_user, update_user_phone
from states.user_states import OrderState
from utils.helpers import format_payment_type, format_price

logger = logging.getLogger(__name__)

router = Router(name="user_order")

# Regex to validate phone numbers: +998 XX XXX XX XX (with or without spaces)
_PHONE_RE = re.compile(r"^\+?998\s?\d{2}\s?\d{3}\s?\d{2}\s?\d{2}$")

# Map callback data suffixes → PaymentType enum members
_PAYMENT_MAP: dict[str, PaymentType] = {
    "cash": PaymentType.CASH,
    "click": PaymentType.CLICK,
    "payme": PaymentType.PAYME,
}


# ──────────────────────────────────────────────
# 1. Checkout – entry point
# ──────────────────────────────────────────────
@router.callback_query(F.data == "checkout")
async def on_checkout(
    callback: CallbackQuery, session, state: FSMContext
) -> None:
    """Verify the cart isn't empty and start the order FSM."""
    try:
        await callback.answer()
        cart_items = await get_cart(session, callback.from_user.id)

        if not cart_items:
            await callback.answer(
                "🛒 Savatcha bo'sh! Avval mahsulot qo'shing.",
                show_alert=True,
            )
            return

        await state.set_state(OrderState.address)
        await callback.message.edit_text(
            "📍 Yetkazib berish manzilini kiriting:\n\n"
            "Masalan: Toshkent sh., Chilonzor t., 5-mavze, 10-uy"
        )
    except Exception as e:
        logger.exception("Error starting checkout: %s", e)
        await callback.answer("⚠️ Xatolik yuz berdi", show_alert=True)


# ──────────────────────────────────────────────
# 2. Address
# ──────────────────────────────────────────────
@router.message(OrderState.address)
async def process_address(
    message: Message, session, state: FSMContext
) -> None:
    """Save the delivery address and ask for a phone number."""
    try:
        address = message.text
        if not address or len(address.strip()) < 5:
            await message.answer(
                "❌ Manzil juda qisqa. Iltimos, to'liq manzilni kiriting."
            )
            return

        await state.update_data(address=address.strip())

        # Pre-fill phone from DB if available
        user = await get_user(session, message.from_user.id)
        hint = ""
        if user and user.phone:
            hint = f"\n\n📱 Oldingi raqamingiz: {user.phone}"

        await state.set_state(OrderState.phone)
        await message.answer(
            "📞 Telefon raqamingizni yuboring.\n\n"
            "Kontaktingizni ulashish tugmasini bosing yoki qo'lda "
            "yozing (masalan: +998901234567)." + hint,
            reply_markup=phone_kb(),
        )
    except Exception as e:
        logger.exception("Error processing address: %s", e)
        await message.answer("⚠️ Xatolik yuz berdi. Qaytadan urinib ko'ring.")


# ──────────────────────────────────────────────
# 3. Phone
# ──────────────────────────────────────────────
@router.message(OrderState.phone, F.contact)
async def process_phone_contact(
    message: Message, session, state: FSMContext
) -> None:
    """Accept a shared contact as the phone number."""
    try:
        phone = message.contact.phone_number
        if not phone.startswith("+"):
            phone = f"+{phone}"

        await state.update_data(phone=phone)
        await update_user_phone(session, message.from_user.id, phone)

        await _ask_payment(message, session, state)
    except Exception as e:
        logger.exception("Error processing phone contact: %s", e)
        await message.answer("⚠️ Xatolik yuz berdi. Qaytadan urinib ko'ring.")


@router.message(OrderState.phone)
async def process_phone_text(
    message: Message, session, state: FSMContext
) -> None:
    """Accept a manually typed phone number."""
    try:
        phone = message.text.strip() if message.text else ""

        if not _PHONE_RE.match(phone):
            await message.answer(
                "❌ Noto'g'ri format. Iltimos, raqamni "
                "+998XXXXXXXXX formatida kiriting."
            )
            return

        # Normalise to digits only with leading +
        phone_clean = "+" + re.sub(r"\D", "", phone)
        await state.update_data(phone=phone_clean)
        await update_user_phone(session, message.from_user.id, phone_clean)

        await _ask_payment(message, session, state)
    except Exception as e:
        logger.exception("Error processing phone text: %s", e)
        await message.answer("⚠️ Xatolik yuz berdi. Qaytadan urinib ko'ring.")


async def _ask_payment(
    message: Message, session, state: FSMContext
) -> None:
    """Move to the payment state and show available payment methods."""
    toggles = await get_payment_toggles(session)
    await state.set_state(OrderState.payment)
    await message.answer(
        "💳 To'lov turini tanlang:",
        reply_markup=payment_kb(toggles),
    )


# ──────────────────────────────────────────────
# 4. Payment selection
# ──────────────────────────────────────────────
@router.callback_query(OrderState.payment, F.data.startswith("pay:"))
async def process_payment(
    callback: CallbackQuery, session, state: FSMContext
) -> None:
    """Save the chosen payment type and show an order summary."""
    try:
        await callback.answer()
        pay_key = callback.data.split(":")[1]
        payment_type = _PAYMENT_MAP.get(pay_key)

        if payment_type is None:
            await callback.answer(
                "❌ Noto'g'ri to'lov turi", show_alert=True
            )
            return

        await state.update_data(payment_type=payment_type.value)
        data = await state.get_data()

        # Build summary
        cart_items = await get_cart(session, callback.from_user.id)
        total = await get_cart_total(session, callback.from_user.id)
        delivery_price = await get_delivery_price(session)

        lines = ["📋 Buyurtma xulosasi:\n"]
        for item in cart_items:
            item_total = item.quantity * item.product.price
            lines.append(
                f"  {item.product.name} x {item.quantity} = "
                f"{format_price(item_total)}"
            )
        lines.append(f"\n💰 Mahsulotlar: {format_price(total)}")
        if delivery_price:
            lines.append(f"🚚 Yetkazib berish: {format_price(delivery_price)}")
            lines.append(
                f"💵 Jami: {format_price(total + delivery_price)}"
            )
        else:
            lines.append(f"💵 Jami: {format_price(total)}")
        lines.append(f"\n📍 Manzil: {data['address']}")
        lines.append(f"📞 Telefon: {data['phone']}")
        lines.append(
            f"💳 To'lov: {format_payment_type(payment_type)}"
        )

        await state.set_state(OrderState.confirm)
        await callback.message.edit_text(
            "\n".join(lines),
            reply_markup=confirm_order_kb(),
        )
    except Exception as e:
        logger.exception("Error processing payment: %s", e)
        await callback.answer("⚠️ Xatolik yuz berdi", show_alert=True)


# ──────────────────────────────────────────────
# 5a. Confirm order
# ──────────────────────────────────────────────
@router.callback_query(OrderState.confirm, F.data == "order_confirm")
async def confirm_order(
    callback: CallbackQuery,
    session,
    state: FSMContext,
    bot: Bot,
) -> None:
    """Create the order, notify the admin group, and clear state."""
    try:
        await callback.answer()
        data = await state.get_data()

        payment_type = PaymentType(data["payment_type"])

        order = await create_order_from_cart(
            session=session,
            user_id=callback.from_user.id,
            address=data["address"],
            phone=data["phone"],
            payment_type=payment_type,
        )

        # ── Send success to user ──
        await callback.message.edit_text(
            f"✅ Buyurtma #{order.id} muvaffaqiyatli qabul qilindi!\n\n"
            "Tez orada siz bilan bog'lanamiz. Rahmat! 🙏",
        )
        await callback.message.answer(
            "🏠 Bosh menyu:",
            reply_markup=main_menu_kb(),
        )

        # ── Notify admin group ──
        try:
            user = await get_user(session, callback.from_user.id)

            item_lines: list[str] = []
            for item in order.items:
                item_total = item.price * item.quantity
                item_lines.append(
                    f"  {item.product.name} x {item.quantity} = "
                    f"{format_price(item_total)}"
                )

            admin_text = (
                f"🆕 Yangi buyurtma #{order.id}\n\n"
                f"👤 Mijoz: {user.full_name}\n"
                f"📞 Telefon: {order.phone}\n"
                f"📍 Manzil: {order.address}\n"
                f"💳 To'lov: {format_payment_type(order.payment_type)}\n\n"
                f"📦 Mahsulotlar:\n"
                + "\n".join(item_lines)
                + f"\n\n💰 Jami: {format_price(order.total)}"
            )

            await bot.send_message(
                chat_id=settings.ADMIN_GROUP_ID,
                text=admin_text,
                reply_markup=order_status_kb(order.id),
            )
        except Exception as admin_err:
            logger.exception(
                "Failed to send order notification to admin group: %s",
                admin_err,
            )

        await state.clear()
    except Exception as e:
        logger.exception("Error confirming order: %s", e)
        await callback.answer(
            "⚠️ Buyurtmani yaratishda xatolik yuz berdi",
            show_alert=True,
        )


# ──────────────────────────────────────────────
# 5b. Cancel order
# ──────────────────────────────────────────────
@router.callback_query(OrderState.confirm, F.data == "order_cancel")
async def cancel_order(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Cancel the ongoing order flow and return to the main menu."""
    try:
        await callback.answer("❌ Buyurtma bekor qilindi")
        await state.clear()
        await callback.message.edit_text("❌ Buyurtma bekor qilindi.")
        await callback.message.answer(
            "🏠 Bosh menyu:",
            reply_markup=main_menu_kb(),
        )
    except Exception as e:
        logger.exception("Error cancelling order: %s", e)
        await callback.answer("⚠️ Xatolik yuz berdi", show_alert=True)
