"""
Admin product management handlers.
Full CRUD, search, stock/price adjustments.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from locales import get_text
from keyboards.reply import admin_menu_keyboard, admin_products_keyboard
from keyboards.inline import (
    category_select_keyboard,
    product_list_inline_keyboard,
    product_admin_keyboard,
    pagination_keyboard,
    confirm_delete_keyboard,
)
from states.admin_states import AdminStates
from services.category_service import CategoryService
from services.product_service import ProductService
from utils.pagination import Paginator
from utils.misc import format_price

router = Router(name="admin_products")

PRODUCTS_PER_PAGE = 8


# ──────────────────────────────────────────────────────────
# Products menu
# ──────────────────────────────────────────────────────────
@router.message(
    AdminStates.in_admin_menu,
    F.text.in_({"📦 Mahsulotlar", "📦 Продукты"}),
)
async def products_menu(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    await message.answer(
        get_text(lang, "admin_products_menu"),
        reply_markup=admin_products_keyboard(lang),
    )
    await state.set_state(AdminStates.in_products_menu)


# ──────────────────────────────────────────────────────────
# Add product flow (5 steps)
# ──────────────────────────────────────────────────────────

# Step 1 – ask name
@router.message(
    AdminStates.in_products_menu,
    F.text.in_({"➕ Qo'shish", "➕ Добавить"}),
)
async def add_product_start(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    await message.answer(get_text(lang, "enter_product_name"))
    await state.set_state(AdminStates.adding_product_name)


# Step 2 – name entered → ask category
@router.message(AdminStates.adding_product_name, F.text)
async def add_product_name(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    await state.update_data(new_prod_name=message.text.strip())

    categories = await CategoryService.get_all(session)
    if not categories:
        await message.answer(get_text(lang, "no_categories_create_first"))
        await state.set_state(AdminStates.in_products_menu)
        return

    await message.answer(
        get_text(lang, "select_product_category"),
        reply_markup=category_select_keyboard(categories, lang, prefix="prodcat_"),
    )
    await state.set_state(AdminStates.adding_product_category)


# Step 3 – category selected → ask price
@router.callback_query(
    AdminStates.adding_product_category,
    F.data.startswith("prodcat_"),
)
async def add_product_category(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    category_id = int(callback.data.split("_")[-1])
    await state.update_data(new_prod_category_id=category_id)

    await callback.message.edit_text(get_text(lang, "enter_product_price"))
    await state.set_state(AdminStates.adding_product_price)
    await callback.answer()


# Step 4 – price entered → ask image
@router.message(AdminStates.adding_product_price, F.text)
async def add_product_price(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    try:
        price = int(message.text.strip())
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer(get_text(lang, "invalid_price"))
        return

    await state.update_data(new_prod_price=price)
    await message.answer(get_text(lang, "send_product_image"))
    await state.set_state(AdminStates.adding_product_image)


# Step 5a – image received → ask stock
@router.message(AdminStates.adding_product_image, F.photo)
async def add_product_image(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    photo_id = message.photo[-1].file_id
    await state.update_data(new_prod_image=photo_id)

    await message.answer(get_text(lang, "enter_product_stock"))
    await state.set_state(AdminStates.adding_product_stock)


# Step 5b – skip image → ask stock
@router.message(
    AdminStates.adding_product_image,
    F.text.in_({"/skip", "skip", "⏩ O'tkazish", "⏩ Пропустить"}),
)
async def add_product_skip_image(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    await state.update_data(new_prod_image=None)

    await message.answer(get_text(lang, "enter_product_stock"))
    await state.set_state(AdminStates.adding_product_stock)


# Step 6 – stock entered → create product
@router.message(AdminStates.adding_product_stock, F.text)
async def add_product_stock(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    try:
        stock = int(message.text.strip())
        if stock < 0:
            raise ValueError
    except ValueError:
        await message.answer(get_text(lang, "invalid_stock"))
        return

    product = await ProductService.create(
        session,
        name=data.get("new_prod_name"),
        category_id=data.get("new_prod_category_id"),
        price=data.get("new_prod_price"),
        image=data.get("new_prod_image"),
        stock=stock,
    )

    await message.answer(
        get_text(lang, "product_added").format(name=product.name),
        reply_markup=admin_products_keyboard(lang),
    )
    await state.set_state(AdminStates.in_products_menu)


# ──────────────────────────────────────────────────────────
# Product list (all categories, paginated)
# ──────────────────────────────────────────────────────────
@router.message(
    AdminStates.in_products_menu,
    F.text.in_({"📋 Ro'yxat", "📋 Список"}),
)
async def list_products(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    categories = await CategoryService.get_all(session)
    if not categories:
        await message.answer(get_text(lang, "no_categories"))
        return

    # Show category selector first so admin can filter
    await message.answer(
        get_text(lang, "select_category_to_view"),
        reply_markup=category_select_keyboard(categories, lang, prefix="viewcat_"),
    )
    await state.set_state(AdminStates.viewing_product_list)


@router.callback_query(
    AdminStates.viewing_product_list,
    F.data.startswith("viewcat_"),
)
async def list_products_by_cat(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    category_id = int(callback.data.split("_")[-1])

    await state.update_data(admin_cat_id=category_id, admin_page=1)
    await _show_admin_products_page(callback, state, session, category_id, page=1, lang=lang)
    await callback.answer()


@router.callback_query(
    AdminStates.viewing_product_list,
    F.data.in_({"adm_page_next", "adm_page_prev"}),
)
async def paginate_admin_products(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    category_id = data.get("admin_cat_id")
    page = data.get("admin_page", 1)

    if callback.data == "adm_page_next":
        page += 1
    else:
        page = max(1, page - 1)

    await state.update_data(admin_page=page)
    await _show_admin_products_page(callback, state, session, category_id, page, lang)
    await callback.answer()


async def _show_admin_products_page(callback, state, session, category_id, page, lang):
    total = await ProductService.count_by_category(session, category_id)
    offset = (page - 1) * PRODUCTS_PER_PAGE
    products = await ProductService.get_by_category(
        session, category_id, offset=offset, limit=PRODUCTS_PER_PAGE
    )
    paginator = Paginator(total=total, per_page=PRODUCTS_PER_PAGE, current_page=page)

    if not products:
        await callback.message.edit_text(get_text(lang, "no_products"))
        return

    text = get_text(lang, "product_list_admin")
    if paginator.total_pages > 1:
        text += f"\n📄 {page}/{paginator.total_pages}"

    await callback.message.edit_text(
        text,
        reply_markup=product_list_inline_keyboard(products, lang, admin=True),
    )


# ──────────────────────────────────────────────────────────
# View single product (admin)
# ──────────────────────────────────────────────────────────
@router.callback_query(
    AdminStates.viewing_product_list,
    F.data.startswith("view_prod_"),
)
async def admin_view_product(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    product_id = int(callback.data.split("_")[-1])

    product = await ProductService.get_by_id(session, product_id)
    if not product:
        await callback.answer(get_text(lang, "product_not_found"), show_alert=True)
        return

    caption = _admin_product_card(product, lang)
    markup = product_admin_keyboard(product_id, lang)

    try:
        await callback.message.delete()
    except Exception:
        pass

    if product.image:
        await callback.message.answer_photo(
            photo=product.image, caption=caption, reply_markup=markup,
        )
    else:
        await callback.message.answer(caption, reply_markup=markup)

    await state.update_data(admin_prod_id=product_id)
    await callback.answer()


# ──────────────────────────────────────────────────────────
# Edit product  (name / price / stock)
# ──────────────────────────────────────────────────────────
@router.callback_query(
    AdminStates.viewing_product_list,
    F.data.startswith("edit_prod_"),
)
async def edit_product_name_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    product_id = int(callback.data.split("_")[-1])
    await state.update_data(edit_prod_id=product_id)

    await callback.message.answer(get_text(lang, "enter_new_product_name"))
    await state.set_state(AdminStates.editing_product_name)
    await callback.answer()


@router.message(AdminStates.editing_product_name, F.text)
async def edit_product_name_save(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    product_id = data.get("edit_prod_id")

    await ProductService.update(session, product_id, name=message.text.strip())
    await message.answer(
        get_text(lang, "product_updated"),
        reply_markup=admin_products_keyboard(lang),
    )
    await state.set_state(AdminStates.in_products_menu)


@router.callback_query(
    AdminStates.viewing_product_list,
    F.data.startswith("price_prod_"),
)
async def edit_product_price_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    product_id = int(callback.data.split("_")[-1])
    await state.update_data(edit_prod_id=product_id)

    await callback.message.answer(get_text(lang, "enter_new_price"))
    await state.set_state(AdminStates.editing_product_price)
    await callback.answer()


@router.message(AdminStates.editing_product_price, F.text)
async def edit_product_price_save(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    product_id = data.get("edit_prod_id")

    try:
        price = int(message.text.strip())
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer(get_text(lang, "invalid_price"))
        return

    await ProductService.update(session, product_id, price=price)
    await message.answer(
        get_text(lang, "product_updated"),
        reply_markup=admin_products_keyboard(lang),
    )
    await state.set_state(AdminStates.in_products_menu)


@router.callback_query(
    AdminStates.viewing_product_list,
    F.data.startswith("stock_prod_"),
)
async def edit_product_stock_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    product_id = int(callback.data.split("_")[-1])
    await state.update_data(edit_prod_id=product_id)

    await callback.message.answer(get_text(lang, "enter_new_stock"))
    await state.set_state(AdminStates.editing_product_stock)
    await callback.answer()


@router.message(AdminStates.editing_product_stock, F.text)
async def edit_product_stock_save(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    product_id = data.get("edit_prod_id")

    try:
        stock = int(message.text.strip())
        if stock < 0:
            raise ValueError
    except ValueError:
        await message.answer(get_text(lang, "invalid_stock"))
        return

    await ProductService.update(session, product_id, stock=stock)
    await message.answer(
        get_text(lang, "product_updated"),
        reply_markup=admin_products_keyboard(lang),
    )
    await state.set_state(AdminStates.in_products_menu)


# ──────────────────────────────────────────────────────────
# Delete product
# ──────────────────────────────────────────────────────────
@router.callback_query(
    AdminStates.viewing_product_list,
    F.data.startswith("del_prod_"),
)
async def delete_product_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    product_id = int(callback.data.split("_")[-1])
    await state.update_data(del_prod_id=product_id)

    product = await ProductService.get_by_id(session, product_id)
    await callback.message.edit_text(
        get_text(lang, "confirm_delete_product").format(name=product.name),
        reply_markup=confirm_delete_keyboard(lang, prefix="confirm_del_prod"),
    )
    await callback.answer()


@router.callback_query(
    AdminStates.viewing_product_list,
    F.data == "confirm_del_prod_yes",
)
async def delete_product_confirmed(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    product_id = data.get("del_prod_id")

    await ProductService.delete(session, product_id)
    await callback.message.edit_text(get_text(lang, "product_deleted"))
    await callback.message.answer(
        get_text(lang, "admin_products_menu"),
        reply_markup=admin_products_keyboard(lang),
    )
    await state.set_state(AdminStates.in_products_menu)
    await callback.answer()


@router.callback_query(
    AdminStates.viewing_product_list,
    F.data == "confirm_del_prod_no",
)
async def delete_product_cancelled(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    await callback.message.edit_text(get_text(lang, "action_cancelled"))
    await state.set_state(AdminStates.in_products_menu)
    await callback.answer()


# ──────────────────────────────────────────────────────────
# Search products
# ──────────────────────────────────────────────────────────
@router.message(
    AdminStates.in_products_menu,
    F.text.in_({"🔍 Qidirish", "🔍 Поиск"}),
)
async def search_products_start(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    await message.answer(get_text(lang, "enter_search_query"))
    await state.set_state(AdminStates.searching_products)


@router.message(AdminStates.searching_products, F.text)
async def search_products_results(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    query = message.text.strip()

    products = await ProductService.search(session, query, limit=20)
    if not products:
        await message.answer(
            get_text(lang, "no_search_results"),
            reply_markup=admin_products_keyboard(lang),
        )
        await state.set_state(AdminStates.in_products_menu)
        return

    text = get_text(lang, "search_results").format(count=len(products), query=query)
    await message.answer(
        text,
        reply_markup=product_list_inline_keyboard(products, lang, admin=True),
    )
    await state.set_state(AdminStates.viewing_product_list)


# ──────────────────────────────────────────────────────────
# Change price (quick)
# ──────────────────────────────────────────────────────────
@router.message(
    AdminStates.in_products_menu,
    F.text.in_({"💰 Narx o'zgartirish", "💰 Изменить цену"}),
)
async def change_price_start(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    categories = await CategoryService.get_all(session)
    if not categories:
        await message.answer(get_text(lang, "no_categories"))
        return

    await message.answer(
        get_text(lang, "select_category_to_view"),
        reply_markup=category_select_keyboard(categories, lang, prefix="pricecat_"),
    )
    await state.set_state(AdminStates.selecting_price_product)


@router.callback_query(
    AdminStates.selecting_price_product,
    F.data.startswith("pricecat_"),
)
async def change_price_category(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    category_id = int(callback.data.split("_")[-1])

    products = await ProductService.get_by_category(session, category_id, offset=0, limit=50)
    if not products:
        await callback.message.edit_text(get_text(lang, "no_products"))
        await state.set_state(AdminStates.in_products_menu)
        await callback.answer()
        return

    await callback.message.edit_text(
        get_text(lang, "select_product"),
        reply_markup=product_list_inline_keyboard(products, lang, admin=True, prefix="priceprod_"),
    )
    await callback.answer()


@router.callback_query(
    AdminStates.selecting_price_product,
    F.data.startswith("priceprod_"),
)
async def change_price_product_selected(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    product_id = int(callback.data.split("_")[-1])
    await state.update_data(edit_prod_id=product_id)

    await callback.message.answer(get_text(lang, "enter_new_price"))
    await state.set_state(AdminStates.editing_product_price)
    await callback.answer()


# ──────────────────────────────────────────────────────────
# Change stock (quick)
# ──────────────────────────────────────────────────────────
@router.message(
    AdminStates.in_products_menu,
    F.text.in_({"📦 Zaxira o'zgartirish", "📦 Изменить остаток"}),
)
async def change_stock_start(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    categories = await CategoryService.get_all(session)
    if not categories:
        await message.answer(get_text(lang, "no_categories"))
        return

    await message.answer(
        get_text(lang, "select_category_to_view"),
        reply_markup=category_select_keyboard(categories, lang, prefix="stockcat_"),
    )
    await state.set_state(AdminStates.selecting_stock_product)


@router.callback_query(
    AdminStates.selecting_stock_product,
    F.data.startswith("stockcat_"),
)
async def change_stock_category(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    category_id = int(callback.data.split("_")[-1])

    products = await ProductService.get_by_category(session, category_id, offset=0, limit=50)
    if not products:
        await callback.message.edit_text(get_text(lang, "no_products"))
        await state.set_state(AdminStates.in_products_menu)
        await callback.answer()
        return

    await callback.message.edit_text(
        get_text(lang, "select_product"),
        reply_markup=product_list_inline_keyboard(products, lang, admin=True, prefix="stockprod_"),
    )
    await callback.answer()


@router.callback_query(
    AdminStates.selecting_stock_product,
    F.data.startswith("stockprod_"),
)
async def change_stock_product_selected(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    product_id = int(callback.data.split("_")[-1])
    await state.update_data(edit_prod_id=product_id)

    await callback.message.answer(get_text(lang, "enter_new_stock"))
    await state.set_state(AdminStates.editing_product_stock)
    await callback.answer()


# ──────────────────────────────────────────────────────────
# Back to admin menu
# ──────────────────────────────────────────────────────────
@router.message(
    AdminStates.in_products_menu,
    F.text.in_({"⬅️ Ortga", "⬅️ Назад"}),
)
async def back_to_admin(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    await message.answer(
        get_text(lang, "admin_menu"),
        reply_markup=admin_menu_keyboard(lang),
    )
    await state.set_state(AdminStates.in_admin_menu)


# ──────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────
def _admin_product_card(product, lang: str) -> str:
    stock_text = str(product.stock) if product.stock is not None else "—"
    lines = [
        f"<b>{product.name}</b>",
        f"💰 {get_text(lang, 'price')}: {format_price(product.price)}",
        f"📦 {get_text(lang, 'stock')}: {stock_text}",
        f"🆔 ID: {product.id}",
    ]
    if product.description:
        lines.insert(1, f"📝 {product.description}")
    return "\n".join(lines)
