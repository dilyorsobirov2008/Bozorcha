"""
Catalog handlers – browsing categories, viewing products, quantity controls,
adding to cart, and pagination.
"""

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

from keyboards.user_kb import (
    categories_kb,
    main_menu_kb,
    product_card_kb,
    products_kb,
)
from services.cart import add_to_cart
from services.category import get_categories, get_category
from services.product import get_product, get_products_by_category
from utils.helpers import format_price

logger = logging.getLogger(__name__)

router = Router(name="user_catalog")

# In-memory store for the quantity selector on product cards.
# key = (user_id, product_id) → current quantity
_quantity_cache: dict[tuple[int, int], int] = {}


def _product_text(product) -> str:
    """Format a product card caption."""
    desc = f"\n{product.description}\n" if product.description else "\n"
    return (
        f"📦 {product.name}\n"
        f"{desc}\n"
        f"💰 Narxi: {format_price(product.price)}\n"
        f"📦 Omborda: {product.stock} dona"
    )


# ──────────────────────────────────────────────
# Select a category  →  show products
# ──────────────────────────────────────────────
@router.callback_query(F.data.startswith("cat:"))
async def on_category_selected(callback: CallbackQuery, session) -> None:
    """Show products in the chosen category (first page)."""
    try:
        await callback.answer()
        category_id = int(callback.data.split(":")[1])

        category = await get_category(session, category_id)
        if not category:
            await callback.answer("❌ Kategoriya topilmadi", show_alert=True)
            return

        products = await get_products_by_category(session, category_id)
        if not products:
            await callback.answer(
                "📭 Bu kategoriyada mahsulot yo'q", show_alert=True
            )
            return

        await callback.message.edit_text(
            f"📂 {category.name}\n\nMahsulotni tanlang:",
            reply_markup=products_kb(products, category_id),
        )
    except Exception as e:
        logger.exception("Error selecting category: %s", e)
        await callback.answer("⚠️ Xatolik yuz berdi", show_alert=True)


# ──────────────────────────────────────────────
# View a single product card
# ──────────────────────────────────────────────
@router.callback_query(F.data.startswith("prod:"))
async def on_product_selected(callback: CallbackQuery, session) -> None:
    """Display a product card with photo (if available) and quantity controls."""
    try:
        await callback.answer()
        product_id = int(callback.data.split(":")[1])

        product = await get_product(session, product_id)
        if not product:
            await callback.answer("❌ Mahsulot topilmadi", show_alert=True)
            return

        user_id = callback.from_user.id
        _quantity_cache[(user_id, product_id)] = 1
        quantity = 1

        text = _product_text(product)
        kb = product_card_kb(product, quantity)

        if product.photo_id:
            # Send photo then remove the old inline message
            await callback.message.answer_photo(
                photo=product.photo_id,
                caption=text,
                reply_markup=kb,
            )
            try:
                await callback.message.delete()
            except Exception:
                pass  # message may already be deleted
        else:
            await callback.message.edit_text(text, reply_markup=kb)
    except Exception as e:
        logger.exception("Error viewing product: %s", e)
        await callback.answer("⚠️ Xatolik yuz berdi", show_alert=True)


# ──────────────────────────────────────────────
# Quantity +/-  on product card
# ──────────────────────────────────────────────
@router.callback_query(F.data.regexp(r"^qty:\d+:plus$"))
async def qty_plus(callback: CallbackQuery, session) -> None:
    """Increment product quantity (capped at stock)."""
    try:
        product_id = int(callback.data.split(":")[1])
        product = await get_product(session, product_id)
        if not product:
            await callback.answer("❌ Mahsulot topilmadi", show_alert=True)
            return

        user_id = callback.from_user.id
        key = (user_id, product_id)
        current = _quantity_cache.get(key, 1)

        if current >= product.stock:
            await callback.answer(
                f"📦 Omborda faqat {product.stock} dona mavjud",
                show_alert=True,
            )
            return

        new_qty = current + 1
        _quantity_cache[key] = new_qty

        kb = product_card_kb(product, new_qty)
        try:
            await callback.message.edit_reply_markup(reply_markup=kb)
        except Exception:
            # If message has photo, edit caption instead
            text = _product_text(product)
            await callback.message.edit_caption(caption=text, reply_markup=kb)
        await callback.answer()
    except Exception as e:
        logger.exception("Error qty_plus: %s", e)
        await callback.answer("⚠️ Xatolik yuz berdi", show_alert=True)


@router.callback_query(F.data.regexp(r"^qty:\d+:minus$"))
async def qty_minus(callback: CallbackQuery, session) -> None:
    """Decrement product quantity (min 1)."""
    try:
        product_id = int(callback.data.split(":")[1])
        product = await get_product(session, product_id)
        if not product:
            await callback.answer("❌ Mahsulot topilmadi", show_alert=True)
            return

        user_id = callback.from_user.id
        key = (user_id, product_id)
        current = _quantity_cache.get(key, 1)

        if current <= 1:
            await callback.answer("Minimal miqdor: 1", show_alert=False)
            return

        new_qty = current - 1
        _quantity_cache[key] = new_qty

        kb = product_card_kb(product, new_qty)
        try:
            await callback.message.edit_reply_markup(reply_markup=kb)
        except Exception:
            text = _product_text(product)
            await callback.message.edit_caption(caption=text, reply_markup=kb)
        await callback.answer()
    except Exception as e:
        logger.exception("Error qty_minus: %s", e)
        await callback.answer("⚠️ Xatolik yuz berdi", show_alert=True)


@router.callback_query(F.data.regexp(r"^qty:\d+:current$"))
async def qty_current_noop(callback: CallbackQuery) -> None:
    """Display-only button – just acknowledge the callback."""
    await callback.answer()


# ──────────────────────────────────────────────
# Add to cart
# ──────────────────────────────────────────────
@router.callback_query(F.data.startswith("add_cart:"))
async def on_add_to_cart(callback: CallbackQuery, session) -> None:
    """Add a product to the user's cart."""
    try:
        parts = callback.data.split(":")
        product_id = int(parts[1])
        quantity = int(parts[2])

        product = await get_product(session, product_id)
        if not product:
            await callback.answer("❌ Mahsulot topilmadi", show_alert=True)
            return

        if quantity > product.stock:
            await callback.answer(
                f"📦 Omborda faqat {product.stock} dona mavjud",
                show_alert=True,
            )
            return

        await add_to_cart(
            session=session,
            user_id=callback.from_user.id,
            product_id=product_id,
            quantity=quantity,
        )

        # Reset quantity cache
        _quantity_cache.pop((callback.from_user.id, product_id), None)

        await callback.answer(
            f"✅ {product.name} ({quantity} dona) savatga qo'shildi!",
            show_alert=True,
        )
    except Exception as e:
        logger.exception("Error adding to cart: %s", e)
        await callback.answer("⚠️ Xatolik yuz berdi", show_alert=True)


# ──────────────────────────────────────────────
# Pagination – categories
# ──────────────────────────────────────────────
@router.callback_query(F.data.startswith("page_cat:"))
async def paginate_categories(callback: CallbackQuery, session) -> None:
    """Show the requested page of categories."""
    try:
        await callback.answer()
        page = int(callback.data.split(":")[1])

        categories = await get_categories(session)
        if not categories:
            await callback.answer(
                "📭 Kategoriyalar topilmadi", show_alert=True
            )
            return

        await callback.message.edit_text(
            "📂 Kategoriyalardan birini tanlang:",
            reply_markup=categories_kb(categories, page=page),
        )
    except Exception as e:
        logger.exception("Error paginating categories: %s", e)
        await callback.answer("⚠️ Xatolik yuz berdi", show_alert=True)


# ──────────────────────────────────────────────
# Pagination – products
# ──────────────────────────────────────────────
@router.callback_query(F.data.startswith("page_prod:"))
async def paginate_products(callback: CallbackQuery, session) -> None:
    """Show the requested page of products in a category."""
    try:
        await callback.answer()
        parts = callback.data.split(":")
        category_id = int(parts[1])
        page = int(parts[2])

        category = await get_category(session, category_id)
        products = await get_products_by_category(session, category_id)

        if not products:
            await callback.answer(
                "📭 Mahsulotlar topilmadi", show_alert=True
            )
            return

        await callback.message.edit_text(
            f"📂 {category.name}\n\nMahsulotni tanlang:",
            reply_markup=products_kb(products, category_id, page=page),
        )
    except Exception as e:
        logger.exception("Error paginating products: %s", e)
        await callback.answer("⚠️ Xatolik yuz berdi", show_alert=True)


# ──────────────────────────────────────────────
# Navigation helpers
# ──────────────────────────────────────────────
@router.callback_query(F.data == "back_to_cats")
async def back_to_categories(callback: CallbackQuery, session) -> None:
    """Navigate back to the category list."""
    try:
        await callback.answer()
        categories = await get_categories(session)

        if callback.message.photo:
            # Current message is a photo – send new text message, delete old
            await callback.message.answer(
                "📂 Kategoriyalardan birini tanlang:",
                reply_markup=categories_kb(categories),
            )
            try:
                await callback.message.delete()
            except Exception:
                pass
        else:
            await callback.message.edit_text(
                "📂 Kategoriyalardan birini tanlang:",
                reply_markup=categories_kb(categories),
            )
    except Exception as e:
        logger.exception("Error navigating back to categories: %s", e)
        await callback.answer("⚠️ Xatolik yuz berdi", show_alert=True)


@router.callback_query(F.data.startswith("back_to_prods"))
async def back_to_products(callback: CallbackQuery, session) -> None:
    """Navigate back to the product list of the current category.

    The callback data may be ``back_to_prods`` (plain) or
    ``back_to_prods:{cat_id}`` carrying the category id.
    """
    try:
        await callback.answer()
        parts = callback.data.split(":")
        if len(parts) >= 2:
            category_id = int(parts[1])
        else:
            # Fallback – try the first category
            categories = await get_categories(session)
            category_id = categories[0].id if categories else None

        if category_id is None:
            await callback.answer("❌ Kategoriya topilmadi", show_alert=True)
            return

        category = await get_category(session, category_id)
        products = await get_products_by_category(session, category_id)

        if callback.message.photo:
            await callback.message.answer(
                f"📂 {category.name}\n\nMahsulotni tanlang:",
                reply_markup=products_kb(products, category_id),
            )
            try:
                await callback.message.delete()
            except Exception:
                pass
        else:
            await callback.message.edit_text(
                f"📂 {category.name}\n\nMahsulotni tanlang:",
                reply_markup=products_kb(products, category_id),
            )
    except Exception as e:
        logger.exception("Error navigating back to products: %s", e)
        await callback.answer("⚠️ Xatolik yuz berdi", show_alert=True)


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery) -> None:
    """Delete the inline message and show the reply-keyboard main menu."""
    try:
        await callback.answer()
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(
            "🏠 Bosh menyu:",
            reply_markup=main_menu_kb(),
        )
    except Exception as e:
        logger.exception("Error navigating back to menu: %s", e)
        await callback.answer("⚠️ Xatolik yuz berdi", show_alert=True)
