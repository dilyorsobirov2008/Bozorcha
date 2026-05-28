"""
Catalog / product-browsing handlers.
Uses dynamic categories from the DB and inline keyboards for navigation.
"""

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from locales import get_text
from keyboards.reply import main_menu_keyboard, categories_keyboard
from keyboards.inline import (
    category_select_keyboard,
    product_list_inline_keyboard,
    product_keyboard,
    pagination_keyboard,
)
from states.user_states import UserStates
from services.category_service import CategoryService
from services.product_service import ProductService
from utils.pagination import Paginator
from utils.misc import format_price

router = Router(name="catalog")

PRODUCTS_PER_PAGE = 5


# ──────────────────────────────────────────────────────────
# Shopping button  →  show dynamic category list
# ──────────────────────────────────────────────────────────
@router.message(
    UserStates.in_main_menu,
    F.text.in_({"🛒 Harid qilish", "🛒 Покупки"}),
)
async def show_categories(message: Message, state: FSMContext, session: AsyncSession):
    """Fetch all categories from DB and present them as inline buttons."""
    data = await state.get_data()
    lang = data.get("lang", "uz")

    categories = await CategoryService.get_all(session)
    if not categories:
        await message.answer(get_text(lang, "no_categories"))
        return

    await message.answer(
        get_text(lang, "choose_category"),
        reply_markup=category_select_keyboard(categories, lang),
    )
    await state.set_state(UserStates.browsing_categories)


# ──────────────────────────────────────────────────────────
# Category selected  →  show product list (page 1)
# ──────────────────────────────────────────────────────────
@router.callback_query(
    UserStates.browsing_categories,
    F.data.startswith("select_cat_"),
)
async def category_selected(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Load products for the chosen category and show paginated list."""
    data = await state.get_data()
    lang = data.get("lang", "uz")
    category_id = int(callback.data.split("_")[-1])

    category = await CategoryService.get_by_id(session, category_id)
    if not category:
        await callback.answer(get_text(lang, "category_not_found"), show_alert=True)
        return

    await state.update_data(category_id=category_id, page=1)

    total = await ProductService.count_by_category(session, category_id)
    products = await ProductService.get_by_category(
        session, category_id, offset=0, limit=PRODUCTS_PER_PAGE
    )

    if not products:
        await callback.answer(get_text(lang, "no_products"), show_alert=True)
        return

    paginator = Paginator(total=total, per_page=PRODUCTS_PER_PAGE, current_page=1)

    text = get_text(lang, "products_in_category").format(category=category.name)
    markup = product_list_inline_keyboard(products, lang)

    if paginator.total_pages > 1:
        text += f"\n\n📄 {paginator.current_page}/{paginator.total_pages}"

    await callback.message.edit_text(
        text,
        reply_markup=markup,
    )
    await state.set_state(UserStates.browsing_products)
    await callback.answer()


# ──────────────────────────────────────────────────────────
# Pagination  →  page_next / page_prev
# ──────────────────────────────────────────────────────────
@router.callback_query(
    UserStates.browsing_products,
    F.data.in_({"page_next", "page_prev"}),
)
async def paginate_products(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Navigate between product pages."""
    data = await state.get_data()
    lang = data.get("lang", "uz")
    category_id = data.get("category_id")
    current_page = data.get("page", 1)

    total = await ProductService.count_by_category(session, category_id)
    paginator = Paginator(total=total, per_page=PRODUCTS_PER_PAGE, current_page=current_page)

    if callback.data == "page_next" and paginator.has_next:
        new_page = current_page + 1
    elif callback.data == "page_prev" and paginator.has_prev:
        new_page = current_page - 1
    else:
        await callback.answer()
        return

    offset = (new_page - 1) * PRODUCTS_PER_PAGE
    products = await ProductService.get_by_category(
        session, category_id, offset=offset, limit=PRODUCTS_PER_PAGE
    )
    await state.update_data(page=new_page)

    paginator_new = Paginator(total=total, per_page=PRODUCTS_PER_PAGE, current_page=new_page)
    category = await CategoryService.get_by_id(session, category_id)
    text = get_text(lang, "products_in_category").format(category=category.name)
    text += f"\n\n📄 {paginator_new.current_page}/{paginator_new.total_pages}"

    await callback.message.edit_text(
        text,
        reply_markup=product_list_inline_keyboard(products, lang),
    )
    await callback.answer()


# ──────────────────────────────────────────────────────────
# Product selected  →  show product card
# ──────────────────────────────────────────────────────────
@router.callback_query(
    UserStates.browsing_products,
    F.data.startswith("view_prod_"),
)
async def view_product(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Display a product card with photo (if available), info, and action buttons."""
    data = await state.get_data()
    lang = data.get("lang", "uz")
    product_id = int(callback.data.split("_")[-1])

    product = await ProductService.get_by_id(session, product_id)
    if not product:
        await callback.answer(get_text(lang, "product_not_found"), show_alert=True)
        return

    await state.update_data(product_id=product_id, quantity=1)

    caption = _format_product_card(product, lang, quantity=1)
    markup = product_keyboard(product_id, quantity=1, lang=lang)

    try:
        await callback.message.delete()
    except Exception:
        pass

    if product.image:
        await callback.message.answer_photo(
            photo=product.image,
            caption=caption,
            reply_markup=markup,
        )
    else:
        await callback.message.answer(
            caption,
            reply_markup=markup,
        )

    await state.set_state(UserStates.viewing_product)
    await callback.answer()


# ──────────────────────────────────────────────────────────
# Quantity adjustment  ( minus / plus )
# ──────────────────────────────────────────────────────────
@router.callback_query(
    UserStates.viewing_product,
    F.data.startswith("minus_"),
)
async def decrease_qty(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    product_id = int(callback.data.split("_")[-1])
    qty = max(1, data.get("quantity", 1) - 1)
    await state.update_data(quantity=qty)

    product = await ProductService.get_by_id(session, product_id)
    caption = _format_product_card(product, lang, qty)
    markup = product_keyboard(product_id, quantity=qty, lang=lang)

    try:
        if callback.message.photo:
            await callback.message.edit_caption(caption=caption, reply_markup=markup)
        else:
            await callback.message.edit_text(caption, reply_markup=markup)
    except Exception:
        pass
    await callback.answer()


@router.callback_query(
    UserStates.viewing_product,
    F.data.startswith("plus_"),
)
async def increase_qty(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    product_id = int(callback.data.split("_")[-1])
    product = await ProductService.get_by_id(session, product_id)

    qty = data.get("quantity", 1) + 1
    if product and product.stock and qty > product.stock:
        await callback.answer(get_text(lang, "max_stock_reached"), show_alert=True)
        return

    await state.update_data(quantity=qty)
    caption = _format_product_card(product, lang, qty)
    markup = product_keyboard(product_id, quantity=qty, lang=lang)

    try:
        if callback.message.photo:
            await callback.message.edit_caption(caption=caption, reply_markup=markup)
        else:
            await callback.message.edit_text(caption, reply_markup=markup)
    except Exception:
        pass
    await callback.answer()


# ──────────────────────────────────────────────────────────
# Add to cart
# ──────────────────────────────────────────────────────────
@router.callback_query(
    UserStates.viewing_product,
    F.data.startswith("add_cart_"),
)
async def add_to_cart(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Add the product to the user's cart."""
    data = await state.get_data()
    lang = data.get("lang", "uz")
    parts = callback.data.split("_")  # add_cart_{prod_id}_{qty}
    product_id = int(parts[2])
    qty = int(parts[3]) if len(parts) > 3 else data.get("quantity", 1)

    from services.cart_service import CartService

    await CartService.add_item(session, callback.from_user.id, product_id, qty)
    await callback.answer(get_text(lang, "added_to_cart"), show_alert=True)

    # Return to the product list
    category_id = data.get("category_id")
    if category_id:
        try:
            await callback.message.delete()
        except Exception:
            pass

        total = await ProductService.count_by_category(session, category_id)
        products = await ProductService.get_by_category(
            session, category_id, offset=0, limit=PRODUCTS_PER_PAGE
        )
        category = await CategoryService.get_by_id(session, category_id)
        text = get_text(lang, "products_in_category").format(category=category.name)
        paginator = Paginator(total=total, per_page=PRODUCTS_PER_PAGE, current_page=1)
        if paginator.total_pages > 1:
            text += f"\n\n📄 1/{paginator.total_pages}"

        await callback.message.answer(
            text,
            reply_markup=product_list_inline_keyboard(products, lang),
        )
        await state.update_data(page=1)
        await state.set_state(UserStates.browsing_products)


# ──────────────────────────────────────────────────────────
# Back buttons
# ──────────────────────────────────────────────────────────
@router.callback_query(
    UserStates.browsing_categories,
    F.data == "back_to_menu",
)
async def back_to_menu_from_categories(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
):
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


@router.callback_query(
    UserStates.browsing_products,
    F.data == "back_to_categories",
)
async def back_to_categories(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    categories = await CategoryService.get_all(session)
    await callback.message.edit_text(
        get_text(lang, "choose_category"),
        reply_markup=category_select_keyboard(categories, lang),
    )
    await state.set_state(UserStates.browsing_categories)
    await callback.answer()


@router.callback_query(
    UserStates.viewing_product,
    F.data == "back_to_products",
)
async def back_to_products(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    category_id = data.get("category_id")
    page = data.get("page", 1)

    offset = (page - 1) * PRODUCTS_PER_PAGE
    products = await ProductService.get_by_category(
        session, category_id, offset=offset, limit=PRODUCTS_PER_PAGE
    )
    total = await ProductService.count_by_category(session, category_id)
    category = await CategoryService.get_by_id(session, category_id)

    text = get_text(lang, "products_in_category").format(category=category.name)
    paginator = Paginator(total=total, per_page=PRODUCTS_PER_PAGE, current_page=page)
    if paginator.total_pages > 1:
        text += f"\n\n📄 {paginator.current_page}/{paginator.total_pages}"

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        text,
        reply_markup=product_list_inline_keyboard(products, lang),
    )
    await state.set_state(UserStates.browsing_products)
    await callback.answer()


# ──────────────────────────────────────────────────────────
# Back via reply keyboard (⬅️ Ortga / ⬅️ Назад)
# ──────────────────────────────────────────────────────────
@router.message(
    UserStates.browsing_categories,
    F.text.in_({"⬅️ Ortga", "⬅️ Назад"}),
)
async def back_reply_categories(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    await message.answer(
        get_text(lang, "main_menu"),
        reply_markup=main_menu_keyboard(lang),
    )
    await state.set_state(UserStates.in_main_menu)


@router.message(
    UserStates.browsing_products,
    F.text.in_({"⬅️ Ortga", "⬅️ Назад"}),
)
async def back_reply_products(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    categories = await CategoryService.get_all(session)
    await message.answer(
        get_text(lang, "choose_category"),
        reply_markup=category_select_keyboard(categories, lang),
    )
    await state.set_state(UserStates.browsing_categories)


# ──────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────
def _format_product_card(product, lang: str, quantity: int = 1) -> str:
    """Build a rich product-card caption."""
    price_formatted = format_price(product.price)
    total_formatted = format_price(product.price * quantity)
    stock_text = f"📦 {product.stock}" if product.stock is not None else "♾️"

    lines = [
        f"<b>{product.name}</b>",
        "",
        f"💰 {get_text(lang, 'price')}: {price_formatted}",
        f"📦 {get_text(lang, 'stock')}: {stock_text}",
        "",
        f"🔢 {get_text(lang, 'quantity')}: {quantity}",
        f"💵 {get_text(lang, 'total')}: {total_formatted}",
    ]

    if product.description:
        lines.insert(1, f"📝 {product.description}")

    return "\n".join(lines)
