"""
Shopping-cart handlers.
View cart, update quantities, remove items, clear cart.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from locales import get_text
from keyboards.reply import main_menu_keyboard
from keyboards.inline import cart_keyboard
from states.user_states import UserStates
from services.cart_service import CartService
from utils.misc import format_price

router = Router(name="cart")


# ──────────────────────────────────────────────────────────
# Show cart (reply-keyboard button)
# ──────────────────────────────────────────────────────────
@router.message(
    UserStates.in_main_menu,
    F.text.in_({"🛒 Savatcha", "🛒 Корзина"}),
)
async def show_cart(message: Message, state: FSMContext, session: AsyncSession):
    await _render_cart(message, state, session)


@router.callback_query(F.data == "show_cart")
async def show_cart_cb(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Also reachable via inline button."""
    try:
        await callback.message.delete()
    except Exception:
        pass
    await _render_cart(callback.message, state, session, from_callback=True)
    await callback.answer()


# ──────────────────────────────────────────────────────────
# Update item quantity  ( cart_plus_{item_id}  /  cart_minus_{item_id} )
# ──────────────────────────────────────────────────────────
@router.callback_query(
    UserStates.in_cart,
    F.data.startswith("cart_plus_"),
)
async def cart_increase(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    item_id = int(callback.data.split("_")[-1])
    await CartService.update_quantity(session, item_id, delta=1)
    await _refresh_cart(callback, state, session)


@router.callback_query(
    UserStates.in_cart,
    F.data.startswith("cart_minus_"),
)
async def cart_decrease(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    item_id = int(callback.data.split("_")[-1])
    await CartService.update_quantity(session, item_id, delta=-1)
    await _refresh_cart(callback, state, session)


# ──────────────────────────────────────────────────────────
# Remove single item  ( cart_remove_{item_id} )
# ──────────────────────────────────────────────────────────
@router.callback_query(
    UserStates.in_cart,
    F.data.startswith("cart_remove_"),
)
async def cart_remove_item(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    item_id = int(callback.data.split("_")[-1])
    await CartService.remove_item(session, item_id)
    await _refresh_cart(callback, state, session)


# ──────────────────────────────────────────────────────────
# Clear entire cart
# ──────────────────────────────────────────────────────────
@router.callback_query(
    UserStates.in_cart,
    F.data == "clear_cart",
)
async def clear_cart(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    await CartService.clear(session, callback.from_user.id)

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        get_text(lang, "cart_empty"),
        reply_markup=main_menu_keyboard(lang),
    )
    await state.set_state(UserStates.in_main_menu)
    await callback.answer()


# ──────────────────────────────────────────────────────────
# Back to main menu from cart
# ──────────────────────────────────────────────────────────
@router.callback_query(
    UserStates.in_cart,
    F.data == "back_to_menu",
)
async def back_from_cart(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        get_text(lang, "main_menu"),
        reply_markup=main_menu_keyboard(lang),
    )
    await state.set_state(UserStates.in_main_menu)
    await callback.answer()


# ──────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────
async def _render_cart(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    *,
    from_callback: bool = False,
):
    """Build and send the full cart view."""
    data = await state.get_data()
    lang = data.get("lang", "uz")
    telegram_id = message.chat.id

    items = await CartService.get_items(session, telegram_id)
    if not items:
        await message.answer(get_text(lang, "cart_empty"))
        return

    total = await CartService.get_total(session, telegram_id)
    text = _format_cart(items, total, lang)

    await message.answer(text, reply_markup=cart_keyboard(items, lang))
    await state.set_state(UserStates.in_cart)


async def _refresh_cart(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
):
    """Re-render the cart inline after a change."""
    data = await state.get_data()
    lang = data.get("lang", "uz")
    telegram_id = callback.from_user.id

    items = await CartService.get_items(session, telegram_id)
    if not items:
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(
            get_text(lang, "cart_empty"),
            reply_markup=main_menu_keyboard(lang),
        )
        await state.set_state(UserStates.in_main_menu)
        await callback.answer()
        return

    total = await CartService.get_total(session, telegram_id)
    text = _format_cart(items, total, lang)

    try:
        await callback.message.edit_text(text, reply_markup=cart_keyboard(items, lang))
    except Exception:
        pass
    await callback.answer()


def _format_cart(items, total, lang: str) -> str:
    """Format all cart items into a readable text block."""
    lines = [f"🛒 <b>{get_text(lang, 'your_cart')}</b>", ""]
    for idx, item in enumerate(items, start=1):
        price = format_price(item.product.price)
        subtotal = format_price(item.product.price * item.quantity)
        lines.append(
            f"{idx}. {item.product.name}  x{item.quantity}  —  {subtotal}"
        )
    lines.append("")
    lines.append(f"💰 <b>{get_text(lang, 'cart_total')}: {format_price(total)}</b>")
    return "\n".join(lines)
