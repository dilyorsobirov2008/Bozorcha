"""Admin product management — full CRUD with multi-step FSM, pagination, and search."""

import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from services.product import (
    create_product,
    get_products_by_category,
    get_product,
    update_product,
    delete_product,
    search_products,
)
from services.category import get_categories, get_category
from keyboards.admin_kb import (
    admin_products_kb,
    admin_product_actions_kb,
    admin_product_edit_kb,
    admin_categories_kb,
    confirm_kb,
    back_admin_kb,
    admin_select_category_kb,
    admin_select_category_for_add_kb,
    admin_category_products_kb,
)
from states.admin_states import AddProduct, EditProduct, ProductSearch
from utils.helpers import format_price

router = Router(name="admin_products")
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

def _product_detail_text(product) -> str:
    """Format a single product's details."""
    cat_name = product.category.name if hasattr(product, "category") and product.category else "—"
    return (
        f"📦 <b>{product.name}</b>\n\n"
        f"📂 Kategoriya: {cat_name}\n"
        f"📝 Tavsif: {product.description or '—'}\n"
        f"💰 Narx: {format_price(product.price)}\n"
        f"📊 Qoldiq: {product.stock} ta\n"
    )

async def _show_category_products(target, state: FSMContext, session: AsyncSession, category_id: int) -> None:
    category = await get_category(session, category_id)
    if not category:
        return
        
    per_page = 10
    products, total_count = await get_products_by_category(session, category_id, page=0, per_page=per_page)
    
    import math
    total_pages = math.ceil(total_count / per_page)
    if total_pages == 0:
        total_pages = 1

    emoji = category.emoji if category.emoji else "📁"
    text = f"{emoji} <b>{category.name}</b> kategoriyasidagi tovarlar:\n\n"
    if not products:
        text += "Bu kategoriyada hozircha tovarlar yo'q."
    else:
        text += f"Jami tovarlar soni: {total_count} ta"

    kb = admin_category_products_kb(products, category_id, page=0, total_pages=total_pages)

    if isinstance(target, CallbackQuery):
        try:
            await target.message.edit_text(text, reply_markup=kb)
        except Exception:
            await target.message.answer(text, reply_markup=kb)
        await target.answer()
    else:
        await target.answer(text, reply_markup=kb)

@router.callback_query(F.data.startswith("adm_cat_products:") | F.data.startswith("adm_cat_view:"))
async def cb_view_category_products(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    logger.info("🎯 Triggered callback: view category products")
    if not await _is_admin(callback, state):
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    try:
        cat_id = int(callback.data.split(":")[1])
        await _show_category_products(callback, state, session, cat_id)
    except Exception as exc:
        logger.error("cb_view_category_products error: %s", exc, exc_info=True)
        await callback.answer("❌ Tovarlarni yuklashda xatolik", show_alert=True)

@router.callback_query(F.data.startswith("adm_cat_prod_page:"))
async def cb_cat_product_page(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    logger.info("🎯 Triggered callback: adm_cat_prod_page")
    if not await _is_admin(callback, state):
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    try:
        parts = callback.data.split(":")
        category_id = int(parts[1])
        page = int(parts[2])
        
        category = await get_category(session, category_id)
        if not category:
            await callback.answer("❌ Kategoriya topilmadi", show_alert=True)
            return

        per_page = 10
        products, total_count = await get_products_by_category(session, category_id, page=page, per_page=per_page)
        
        import math
        total_pages = math.ceil(total_count / per_page)
        if total_pages == 0:
            total_pages = 1

        emoji = category.emoji if category.emoji else "📁"
        text = f"{emoji} <b>{category.name}</b> kategoriyasidagi tovarlar:\n\n"
        if not products:
            text += "Bu kategoriyada hozircha tovarlar yo'q."
        else:
            text += f"Jami tovarlar soni: {total_count} ta"

        await callback.message.edit_text(
            text,
            reply_markup=admin_category_products_kb(products, category_id, page=page, total_pages=total_pages),
        )
        await callback.answer()
    except Exception as exc:
        logger.error("cb_cat_product_page error: %s", exc, exc_info=True)
        await callback.answer("❌ Xatolik", show_alert=True)

@router.callback_query(F.data.startswith("adm_prod_add_to_cat:"))
async def cb_add_product_to_category(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    logger.info("🎯 Triggered callback: adm_prod_add_to_cat")
    if not await _is_admin(callback, state):
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    try:
        cat_id = int(callback.data.split(":")[1])
        category = await get_category(session, cat_id)
        if not category:
            await callback.answer("❌ Kategoriya topilmadi", show_alert=True)
            return

        await state.update_data(product_category_id=cat_id)
        await state.set_state(AddProduct.name)
        await callback.message.edit_text(
            f"📂 Kategoriya: <b>{category.name}</b>\n\n📝 Tovar nomini kiriting:",
            reply_markup=back_admin_kb("adm_back_prods"),
        )
        await callback.answer()
    except Exception as exc:
        logger.error("cb_add_product_to_category error: %s", exc, exc_info=True)
        await callback.answer("❌ Xatolik", show_alert=True)

# ── Add product — start ─────────────────────────────────────────────────
@router.callback_query(F.data == "adm_prod_add")
async def cb_add_product(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    logger.info("🎯 Triggered callback: adm_prod_add")
    if not await _is_admin(callback, state):
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    try:
        categories = await get_categories(session)
        if not categories:
            await callback.answer("❌ Avval kategoriya qo'shing!", show_alert=True)
            return

        await state.set_state(AddProduct.category)
        await callback.message.edit_text(
            "📦 <b>Yangi tovar qo'shish</b>\n\n📂 Kategoriyani tanlang:",
            reply_markup=admin_select_category_for_add_kb(categories),
        )
        await callback.answer()
    except Exception as exc:
        logger.error("cb_add_product error: %s", exc, exc_info=True)
        await callback.answer("❌ Xatolik", show_alert=True)

# Step 1: category selected
@router.callback_query(AddProduct.category, F.data.startswith("adm_cat_view:"))
async def process_product_category(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    logger.info("🎯 Triggered callback: process_product_category")
    try:
        cat_id = int(callback.data.split(":")[1])
        category = await get_category(session, cat_id)
        if not category:
            await callback.answer("❌ Kategoriya topilmadi", show_alert=True)
            return

        await state.update_data(product_category_id=cat_id)
        await state.set_state(AddProduct.name)
        await callback.message.edit_text(
            f"📂 Kategoriya: <b>{category.name}</b>\n\n📝 Tovar nomini kiriting:",
            reply_markup=back_admin_kb("adm_back_prods"),
        )
        await callback.answer()
    except Exception as exc:
        logger.error("process_product_category error: %s", exc, exc_info=True)
        await callback.answer("❌ Xatolik", show_alert=True)

# Step 2: name
@router.message(AddProduct.name)
async def process_product_name(message: Message, state: FSMContext) -> None:
    try:
        name = message.text.strip()
        if not name:
            await message.answer("❌ Nom bo'sh bo'lishi mumkin emas. Qayta kiriting:")
            return
        if len(name) > 200:
            await message.answer("❌ Nom 200 ta belgidan oshmasligi kerak.")
            return

        await state.update_data(product_name=name)
        await state.set_state(AddProduct.description)
        await message.answer(
            f"📝 Nomi: <b>{name}</b>\n\n"
            "📄 Tovar tavsifini kiriting\n(yoki /skip bosib o'tkazib yuboring):",
        )
    except Exception as exc:
        logger.error("process_product_name error: %s", exc, exc_info=True)
        await message.answer("❌ Xatolik yuz berdi.")

# Step 3: description
@router.message(AddProduct.description)
async def process_product_description(message: Message, state: FSMContext) -> None:
    try:
        if message.text.strip().lower() == "/skip":
            description = ""
        else:
            description = message.text.strip()

        await state.update_data(product_description=description)
        await state.set_state(AddProduct.price)
        await message.answer("💰 Narxini kiriting (so'mda):")
    except Exception as exc:
        logger.error("process_product_description error: %s", exc, exc_info=True)
        await message.answer("❌ Xatolik yuz berdi.")

# Step 4: price
@router.message(AddProduct.price)
async def process_product_price(message: Message, state: FSMContext) -> None:
    try:
        text = message.text.strip().replace(",", ".").replace(" ", "")
        try:
            price = float(text)
        except ValueError:
            await message.answer("❌ Noto'g'ri format. Raqam kiriting (masalan: 15000):")
            return

        if price <= 0:
            await message.answer("❌ Narx 0 dan katta bo'lishi kerak.")
            return

        await state.update_data(product_price=price)
        await state.set_state(AddProduct.stock)
        await message.answer(
            f"💰 Narx: {format_price(price)}\n\n📊 Qoldiq miqdorini kiriting:",
        )
    except Exception as exc:
        logger.error("process_product_price error: %s", exc, exc_info=True)
        await message.answer("❌ Xatolik yuz berdi.")

# Step 5: stock
@router.message(AddProduct.stock)
async def process_product_stock(message: Message, state: FSMContext) -> None:
    try:
        try:
            stock = int(message.text.strip())
        except ValueError:
            await message.answer("❌ Butun son kiriting (masalan: 100):")
            return

        if stock < 0:
            await message.answer("❌ Qoldiq 0 dan kam bo'lishi mumkin emas.")
            return

        await state.update_data(product_stock=stock)
        await state.set_state(AddProduct.photo)
        await message.answer(
            f"📊 Qoldiq: {stock} ta\n\n📸 Tovar rasmini yuboring\n(yoki /skip bosib o'tkazib yuboring):",
        )
    except Exception as exc:
        logger.error("process_product_stock error: %s", exc, exc_info=True)
        await message.answer("❌ Xatolik yuz berdi.")

# Step 6: photo
@router.message(AddProduct.photo, F.photo)
async def process_product_photo(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        photo_id = message.photo[-1].file_id
        await state.update_data(product_photo=photo_id)
        await _confirm_product(message, state, session)
    except Exception as exc:
        logger.error("process_product_photo error: %s", exc, exc_info=True)
        await message.answer("❌ Xatolik yuz berdi.")

@router.message(AddProduct.photo, F.text)
async def process_product_photo_skip(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        if message.text.strip().lower() == "/skip":
            await state.update_data(product_photo=None)
            await _confirm_product(message, state, session)
        else:
            await message.answer("📸 Rasm yuboring yoki /skip bosing.")
    except Exception as exc:
        logger.error("process_product_photo_skip error: %s", exc, exc_info=True)
        await message.answer("❌ Xatolik yuz berdi.")

async def _confirm_product(message: Message, state: FSMContext, session: AsyncSession) -> None:
    """Show confirmation summary before creating the product."""
    data = await state.get_data()
    category = await get_category(session, data["product_category_id"])
    cat_name = category.name if category else "—"

    desc = data.get("product_description") or "—"
    photo_status = "✅ Bor" if data.get("product_photo") else "❌ Yo'q"

    await state.set_state(AddProduct.confirm)
    await message.answer(
        "📦 <b>Tovar ma'lumotlari:</b>\n\n"
        f"📂 Kategoriya: {cat_name}\n"
        f"📝 Nomi: {data['product_name']}\n"
        f"📄 Tavsif: {desc}\n"
        f"💰 Narx: {format_price(data['product_price'])}\n"
        f"📊 Qoldiq: {data['product_stock']} ta\n"
        f"📸 Rasm: {photo_status}\n\n"
        "✅ Tasdiqlaysizmi?",
        reply_markup=confirm_kb("adm_prod_add_confirm"),
    )

# Step 7: confirm
@router.callback_query(AddProduct.confirm, F.data == "adm_prod_add_confirm_yes")
async def cb_confirm_add_product(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    logger.info("🎯 Triggered callback: adm_prod_add_confirm_yes")
    try:
        data = await state.get_data()
        product = await create_product(
            session=session,
            category_id=data["product_category_id"],
            name=data["product_name"],
            description=data.get("product_description", ""),
            price=data["product_price"],
            stock=data["product_stock"],
            photo_id=data.get("product_photo"),
        )
        cat_id = data["product_category_id"]
        await state.clear()
        await state.update_data(admin_authenticated=True) # preserve auth state

        logger.info("Product created: id=%s name=%s", product.id, product.name)
        await callback.message.answer(
            f"✅ Tovar muvaffaqiyatli yaratildi!\n\n📦 <b>{product.name}</b>\n💰 {format_price(product.price)}",
        )
        await callback.answer("✅ Yaratildi")

        # Show product list of the category
        await _show_category_products(callback, state, session, cat_id)
    except Exception as exc:
        logger.error("cb_confirm_add_product error: %s", exc, exc_info=True)
        await callback.answer("❌ Xatolik", show_alert=True)

@router.callback_query(AddProduct.confirm, F.data == "adm_prod_add_confirm_no")
async def cb_cancel_add_product(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    logger.info("🎯 Triggered callback: adm_prod_add_confirm_no")
    data = await state.get_data()
    cat_id = data.get("product_category_id")
    await state.clear()
    await state.update_data(admin_authenticated=True) # preserve auth state
    await callback.answer("🚫 Bekor qilindi")
    if cat_id:
        await _show_category_products(callback, state, session, cat_id)
    else:
        categories = await get_categories(session)
        await callback.message.edit_text(
            "📦 <b>Tovarlar boshqaruvi</b>\n\nKategoriya tanlang:",
            reply_markup=admin_select_category_kb(categories),
        )

# ── View product ─────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("adm_prod_view:"))
async def cb_view_product(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    logger.info("🎯 Triggered callback: adm_prod_view")
    if not await _is_admin(callback, state):
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    try:
        prod_id = int(callback.data.split(":")[1])
        product = await get_product(session, prod_id)
        if not product:
            await callback.answer("❌ Tovar topilmadi", show_alert=True)
            return

        text = _product_detail_text(product)

        if hasattr(product, "photo_id") and product.photo_id:
            try:
                await callback.message.delete()
            except Exception:
                pass
            await callback.message.answer_photo(
                photo=product.photo_id,
                caption=text,
                reply_markup=admin_product_actions_kb(prod_id),
            )
        else:
            await callback.message.edit_text(
                text,
                reply_markup=admin_product_actions_kb(prod_id),
            )
        await callback.answer()
    except Exception as exc:
        logger.error("cb_view_product error: %s", exc, exc_info=True)
        await callback.answer("❌ Xatolik", show_alert=True)

# ── Edit product menu ────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("adm_prod_edit:"))
async def cb_edit_product_menu(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    logger.info("🎯 Triggered callback: adm_prod_edit")
    if not await _is_admin(callback, state):
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    try:
        prod_id = int(callback.data.split(":")[1])
        product = await get_product(session, prod_id)
        if not product:
            await callback.answer("❌ Tovar topilmadi", show_alert=True)
            return

        await callback.message.edit_text(
            f"✏️ <b>{product.name}</b> — nimani tahrirlaysiz?",
            reply_markup=admin_product_edit_kb(prod_id),
        )
        await callback.answer()
    except Exception as exc:
        logger.error("cb_edit_product_menu error: %s", exc, exc_info=True)
        await callback.answer("❌ Xatolik", show_alert=True)

# ── Individual edit fields ───────────────────────────────────────────────
@router.callback_query(F.data.startswith("adm_prod_edit_name:"))
async def cb_edit_product_name(callback: CallbackQuery, state: FSMContext) -> None:
    logger.info("🎯 Triggered callback: adm_prod_edit_name")
    if not await _is_admin(callback, state):
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    try:
        prod_id = int(callback.data.split(":")[1])
        await state.update_data(edit_product_id=prod_id, edit_field="name")
        await state.set_state(EditProduct.value)
        await callback.message.edit_text(
            "📝 Yangi tovar nomini kiriting:",
            reply_markup=back_admin_kb(f"adm_prod_view:{prod_id}"),
        )
        await callback.answer()
    except Exception as exc:
        logger.error("cb_edit_product_name error: %s", exc, exc_info=True)
        await callback.answer("❌ Xatolik", show_alert=True)

@router.callback_query(F.data.startswith("adm_prod_edit_desc:"))
async def cb_edit_product_desc(callback: CallbackQuery, state: FSMContext) -> None:
    logger.info("🎯 Triggered callback: adm_prod_edit_desc")
    if not await _is_admin(callback, state):
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    try:
        prod_id = int(callback.data.split(":")[1])
        await state.update_data(edit_product_id=prod_id, edit_field="description")
        await state.set_state(EditProduct.value)
        await callback.message.edit_text(
            "📄 Yangi tavsifni kiriting:",
            reply_markup=back_admin_kb(f"adm_prod_view:{prod_id}"),
        )
        await callback.answer()
    except Exception as exc:
        logger.error("cb_edit_product_desc error: %s", exc, exc_info=True)
        await callback.answer("❌ Xatolik", show_alert=True)

@router.callback_query(F.data.startswith("adm_prod_edit_price:"))
async def cb_edit_product_price(callback: CallbackQuery, state: FSMContext) -> None:
    logger.info("🎯 Triggered callback: adm_prod_edit_price")
    if not await _is_admin(callback, state):
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    try:
        prod_id = int(callback.data.split(":")[1])
        await state.update_data(edit_product_id=prod_id, edit_field="price")
        await state.set_state(EditProduct.value)
        await callback.message.edit_text(
            "💰 Yangi narxni kiriting (so'mda):",
            reply_markup=back_admin_kb(f"adm_prod_view:{prod_id}"),
        )
        await callback.answer()
    except Exception as exc:
        logger.error("cb_edit_product_price error: %s", exc, exc_info=True)
        await callback.answer("❌ Xatolik", show_alert=True)

@router.callback_query(F.data.startswith("adm_prod_edit_stock:"))
async def cb_edit_product_stock(callback: CallbackQuery, state: FSMContext) -> None:
    logger.info("🎯 Triggered callback: adm_prod_edit_stock")
    if not await _is_admin(callback, state):
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    try:
        prod_id = int(callback.data.split(":")[1])
        await state.update_data(edit_product_id=prod_id, edit_field="stock")
        await state.set_state(EditProduct.value)
        await callback.message.edit_text(
            "📊 Yangi qoldiq miqdorini kiriting:",
            reply_markup=back_admin_kb(f"adm_prod_view:{prod_id}"),
        )
        await callback.answer()
    except Exception as exc:
        logger.error("cb_edit_product_stock error: %s", exc, exc_info=True)
        await callback.answer("❌ Xatolik", show_alert=True)

@router.callback_query(F.data.startswith("adm_prod_edit_photo:"))
async def cb_edit_product_photo(callback: CallbackQuery, state: FSMContext) -> None:
    logger.info("🎯 Triggered callback: adm_prod_edit_photo")
    if not await _is_admin(callback, state):
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    try:
        prod_id = int(callback.data.split(":")[1])
        await state.update_data(edit_product_id=prod_id, edit_field="photo_id")
        await state.set_state(EditProduct.value)
        await callback.message.edit_text(
            "📸 Yangi rasm yuboring:",
            reply_markup=back_admin_kb(f"adm_prod_view:{prod_id}"),
        )
        await callback.answer()
    except Exception as exc:
        logger.error("cb_edit_product_photo error: %s", exc, exc_info=True)
        await callback.answer("❌ Xatolik", show_alert=True)

# ── Process edit value (text) ────────────────────────────────────────────
@router.message(EditProduct.value, F.text)
async def process_edit_product_text(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        data = await state.get_data()
        prod_id = data.get("edit_product_id")
        field = data.get("edit_field", "name")
        raw = message.text.strip()

        if not raw:
            await message.answer("❌ Qiymat bo'sh bo'lishi mumkin emas.")
            return

        # Validate & cast
        if field == "price":
            try:
                value = float(raw.replace(",", ".").replace(" ", ""))
            except ValueError:
                await message.answer("❌ Noto'g'ri narx formati. Raqam kiriting.")
                return
            if value <= 0:
                await message.answer("❌ Narx 0 dan katta bo'lishi kerak.")
                return
        elif field == "stock":
            try:
                value = int(raw)
            except ValueError:
                await message.answer("❌ Butun son kiriting.")
                return
            if value < 0:
                await message.answer("❌ Qoldiq 0 dan kam bo'lishi mumkin emas.")
                return
        else:
            value = raw

        product = await update_product(session, prod_id, **{field: value})
        await state.clear()
        await state.update_data(admin_authenticated=True) # preserve auth state

        if product:
            logger.info("Product updated: id=%s field=%s", prod_id, field)
            await message.answer(
                f"✅ Tovar yangilandi!\n\n{_product_detail_text(product)}",
                reply_markup=admin_product_actions_kb(prod_id),
            )
        else:
            await message.answer("❌ Tovar topilmadi.")
    except Exception as exc:
        logger.error("process_edit_product_text error: %s", exc, exc_info=True)
        await state.clear()
        await message.answer("❌ Tovarni yangilashda xatolik.")

# ── Process edit value (photo) ───────────────────────────────────────────
@router.message(EditProduct.value, F.photo)
async def process_edit_product_photo(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        data = await state.get_data()
        prod_id = data.get("edit_product_id")
        field = data.get("edit_field")

        if field != "photo_id":
            await message.answer("❌ Matn kiriting, rasm emas.")
            return

        photo_id = message.photo[-1].file_id
        product = await update_product(session, prod_id, photo_id=photo_id)
        await state.clear()
        await state.update_data(admin_authenticated=True) # preserve auth state

        if product:
            logger.info("Product photo updated: id=%s", prod_id)
            await message.answer(
                f"✅ Rasm yangilandi!\n\n{_product_detail_text(product)}",
                reply_markup=admin_product_actions_kb(prod_id),
            )
        else:
            await message.answer("❌ Tovar topilmadi.")
    except Exception as exc:
        logger.error("process_edit_product_photo error: %s", exc, exc_info=True)
        await state.clear()
        await message.answer("❌ Rasmni yangilashda xatolik.")

# ── Delete product ───────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("adm_prod_del:"))
async def cb_delete_product(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    logger.info("🎯 Triggered callback: adm_prod_del")
    if not await _is_admin(callback, state):
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    try:
        prod_id = int(callback.data.split(":")[1])
        product = await get_product(session, prod_id)
        if not product:
            await callback.answer("❌ Tovar topilmadi", show_alert=True)
            return

        await callback.message.edit_text(
            f"⚠️ <b>Tovarni o'chirish</b>\n\n📦 <b>{product.name}</b>\n💰 {format_price(product.price)}\n\nHaqiqatan ham o'chirmoqchimisiz?",
            reply_markup=confirm_kb(f"adm_prod_del_confirm:{prod_id}"),
        )
        await callback.answer()
    except Exception as exc:
        logger.error("cb_delete_product error: %s", exc, exc_info=True)
        await callback.answer("❌ Xatolik", show_alert=True)

@router.callback_query(F.data.regexp(r"^adm_prod_del_confirm:\d+_yes$"))
async def cb_delete_product_yes(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    logger.info("🎯 Triggered callback: adm_prod_del_confirm_yes")
    if not await _is_admin(callback, state):
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    try:
        parts = callback.data.replace("adm_prod_del_confirm:", "").replace("_yes", "")
        prod_id = int(parts)
        
        product = await get_product(session, prod_id)
        cat_id = product.category_id if product else None

        success = await delete_product(session, prod_id)
        if success:
            logger.info("Product deleted: id=%s", prod_id)
            await callback.answer("✅ Tovar o'chirildi")
        else:
            await callback.answer("❌ Tovar topilmadi", show_alert=True)

        if cat_id:
            await _show_category_products(callback, state, session, cat_id)
        else:
            categories = await get_categories(session)
            await callback.message.edit_text(
                "📦 <b>Tovarlar boshqaruvi</b>\n\nKategoriya tanlang:",
                reply_markup=admin_select_category_kb(categories),
            )
    except Exception as exc:
        logger.error("cb_delete_product_yes error: %s", exc, exc_info=True)
        await callback.answer("❌ Xatolik", show_alert=True)

@router.callback_query(F.data.regexp(r"^adm_prod_del_confirm:\d+_no$"))
async def cb_delete_product_no(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    logger.info("🎯 Triggered callback: adm_prod_del_confirm_no")
    await callback.answer("🚫 Bekor qilindi")
    try:
        parts = callback.data.replace("adm_prod_del_confirm:", "").replace("_no", "")
        prod_id = int(parts)
        product = await get_product(session, prod_id)
        if product:
            await callback.message.edit_text(
                _product_detail_text(product),
                reply_markup=admin_product_actions_kb(prod_id),
            )
    except Exception:
        pass

# ── Pagination ───────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("adm_prod_page:"))
async def cb_product_page(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    logger.info("🎯 Triggered callback: adm_prod_page")
    if not await _is_admin(callback, state):
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    try:
        categories = await get_categories(session)
        await callback.message.edit_text(
            "📦 <b>Tovarlar boshqaruvi</b>\n\nKategoriya tanlang:",
            reply_markup=admin_select_category_kb(categories),
        )
        await callback.answer()
    except Exception as exc:
        logger.error("cb_product_page error: %s", exc, exc_info=True)
        await callback.answer("❌ Xatolik", show_alert=True)

# ── Search ───────────────────────────────────────────────────────────────
@router.callback_query(F.data == "adm_prod_search")
async def cb_product_search(callback: CallbackQuery, state: FSMContext) -> None:
    logger.info("🎯 Triggered callback: adm_prod_search")
    if not await _is_admin(callback, state):
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    try:
        await state.set_state(ProductSearch.query)
        await callback.message.edit_text(
            "🔍 <b>Tovar qidirish</b>\n\nTovar nomini kiriting:",
            reply_markup=back_admin_kb("adm_back_prods"),
        )
        await callback.answer()
    except Exception as exc:
        logger.error("cb_product_search error: %s", exc, exc_info=True)
        await callback.answer("❌ Xatolik", show_alert=True)

@router.message(ProductSearch.query, F.text)
async def handle_product_search_query(message: Message, state: FSMContext, session: AsyncSession) -> None:
    """Catch text messages when search is expected."""
    if not await _is_admin(message, state):
        return

    try:
        await state.clear()
        await state.update_data(admin_authenticated=True) # preserve auth state
        query = message.text.strip()
        if not query:
            await message.answer("❌ Qidiruv so'zi bo'sh. Qayta urinib ko'ring.")
            return

        products, total_count = await search_products(session, query, per_page=100)
        if not products:
            await message.answer(
                f'🔍 "<b>{query}</b>" bo\'yicha hech narsa topilmadi.',
                reply_markup=back_admin_kb("adm_back_prods"),
            )
            return

        lines = [f'🔍 "<b>{query}</b>" bo\'yicha natijalar: {total_count} ta\n']
        for p in products[:20]:
            lines.append(f"📦 {p.name} — {format_price(p.price)}")

        await message.answer("\n".join(lines), reply_markup=back_admin_kb("adm_back_prods"))
    except Exception as exc:
        logger.error("handle_product_search_query error: %s", exc, exc_info=True)
        await message.answer("❌ Qidiruvda xatolik.")

# ── Back to products ─────────────────────────────────────────────────────
@router.callback_query(F.data == "adm_back_prods")
async def cb_back_to_products(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    logger.info("🎯 Triggered callback: adm_back_prods")
    if not await _is_admin(callback, state):
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    try:
        await state.clear()
        await state.update_data(admin_authenticated=True) # preserve auth state
        categories = await get_categories(session)
        await callback.message.edit_text(
            "📦 <b>Tovarlar boshqaruvi</b>\n\nKategoriya tanlang:",
            reply_markup=admin_select_category_kb(categories),
        )
        await callback.answer()
    except Exception as exc:
        logger.error("cb_back_to_products error: %s", exc, exc_info=True)
        await callback.answer("❌ Xatolik", show_alert=True)
