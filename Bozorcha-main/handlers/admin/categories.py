"""Admin category management — add / edit / delete categories via FSM & callbacks."""

import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from services.category import (
    create_category,
    get_categories,
    get_category,
    update_category,
    delete_category,
)
from keyboards.admin_kb import (
    admin_categories_kb,
    admin_category_edit_kb,
    confirm_kb,
    back_admin_kb,
)
from states.admin_states import AddCategory, EditCategory

router = Router(name="admin_categories")
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

async def _show_categories(target, state: FSMContext, session: AsyncSession) -> None:
    """Send the category list (works for both Message & CallbackQuery)."""
    categories = await get_categories(session)
    if not categories:
        text = "📂 Kategoriyalar bo'sh.\nYangi kategoriya qo'shish uchun tugmani bosing."
    else:
        lines = ["📂 <b>Kategoriyalar ro'yxati:</b>\n"]
        for i, cat in enumerate(categories, 1):
            emoji = cat.emoji if cat.emoji else "📁"
            lines.append(f"{i}. {emoji} {cat.name}")
        text = "\n".join(lines)

    kb = admin_categories_kb(categories)

    if isinstance(target, CallbackQuery):
        try:
            await target.message.edit_text(text, reply_markup=kb)
        except Exception:
            await target.message.answer(text, reply_markup=kb)
        await target.answer()
    else:
        await target.answer(text, reply_markup=kb)

# ── Add category ─────────────────────────────────────────────────────────
@router.callback_query(F.data == "adm_cat_add")
async def cb_add_category(callback: CallbackQuery, state: FSMContext) -> None:
    logger.info("🎯 Triggered callback: adm_cat_add")
    if not await _is_admin(callback, state):
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    try:
        await state.set_state(AddCategory.name)
        await callback.message.edit_text(
            "📂 <b>Yangi kategoriya</b>\n\n📝 Kategoriya nomini kiriting:",
            reply_markup=back_admin_kb(),
        )
        await callback.answer()
    except Exception as exc:
        logger.error("cb_add_category error: %s", exc, exc_info=True)
        await callback.answer("❌ Xatolik", show_alert=True)

@router.message(AddCategory.name)
async def process_category_name(message: Message, state: FSMContext) -> None:
    try:
        name = message.text.strip()
        if not name:
            await message.answer("❌ Nom bo'sh bo'lishi mumkin emas. Qayta kiriting:")
            return
        if len(name) > 100:
            await message.answer("❌ Nom 100 ta belgidan oshmasligi kerak. Qayta kiriting:")
            return

        await state.update_data(category_name=name)
        await state.set_state(AddCategory.emoji)
        await message.answer(
            f"📝 Kategoriya nomi: <b>{name}</b>\n\n😀 Endi emoji tanlang (masalan: 🍎, 🥛, 🧴):",
            reply_markup=back_admin_kb(),
        )
    except Exception as exc:
        logger.error("process_category_name error: %s", exc, exc_info=True)
        await state.clear()
        await message.answer("❌ Xatolik yuz berdi.")

@router.message(AddCategory.emoji)
async def process_category_emoji(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        emoji = message.text.strip()
        if not emoji:
            await message.answer("❌ Emoji bo'sh bo'lishi mumkin emas. Qayta kiriting:")
            return

        data = await state.get_data()
        name = data.get("category_name", "")

        category = await create_category(session=session, name=name, emoji=emoji)
        await state.set_state(None)
        await state.update_data(admin_authenticated=True) # preserve auth state

        logger.info("Category created: id=%s name=%s", category.id, name)
        await message.answer(f"✅ Kategoriya yaratildi!\n\n{emoji} <b>{name}</b>")
        
        # Show updated list
        categories = await get_categories(session)
        await message.answer(
            "📂 <b>Kategoriyalar:</b>",
            reply_markup=admin_categories_kb(categories),
        )
    except Exception as exc:
        logger.error("process_category_emoji error: %s", exc, exc_info=True)
        await state.clear()
        await message.answer("❌ Kategoriya yaratishda xatolik yuz berdi.")

# ── Edit category ────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("adm_cat_edit:"))
async def cb_category_edit_menu(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    logger.info("🎯 Triggered callback: adm_cat_edit")
    if not await _is_admin(callback, state):
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    try:
        cat_id = int(callback.data.split(":")[1])
        category = await get_category(session, cat_id)
        if not category:
            await callback.answer("❌ Kategoriya topilmadi", show_alert=True)
            return

        emoji = category.emoji if category.emoji else "📁"
        await callback.message.edit_text(
            f"✏️ <b>Kategoriyani tahrirlash</b>\n\n"
            f"{emoji} <b>{category.name}</b>\n\n"
            f"Nimani o'zgartirmoqchisiz?",
            reply_markup=admin_category_edit_kb(cat_id),
        )
        await callback.answer()
    except Exception as exc:
        logger.error("cb_category_edit_menu error: %s", exc, exc_info=True)
        await callback.answer("❌ Xatolik", show_alert=True)

@router.callback_query(F.data.startswith("adm_cat_edit_name:"))
async def cb_edit_category_name(callback: CallbackQuery, state: FSMContext) -> None:
    logger.info("🎯 Triggered callback: adm_cat_edit_name")
    if not await _is_admin(callback, state):
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    try:
        cat_id = int(callback.data.split(":")[1])
        await state.update_data(edit_category_id=cat_id, edit_field="name")
        await state.set_state(EditCategory.value)
        await callback.message.edit_text(
            "✏️ Yangi kategoriya nomini kiriting:",
            reply_markup=back_admin_kb("adm_back_cats"),
        )
        await callback.answer()
    except Exception as exc:
        logger.error("cb_edit_category_name error: %s", exc, exc_info=True)
        await callback.answer("❌ Xatolik", show_alert=True)

@router.callback_query(F.data.startswith("adm_cat_edit_emoji:"))
async def cb_edit_category_emoji(callback: CallbackQuery, state: FSMContext) -> None:
    logger.info("🎯 Triggered callback: adm_cat_edit_emoji")
    if not await _is_admin(callback, state):
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    try:
        cat_id = int(callback.data.split(":")[1])
        await state.update_data(edit_category_id=cat_id, edit_field="emoji")
        await state.set_state(EditCategory.value)
        await callback.message.edit_text(
            "😀 Yangi emoji kiriting:",
            reply_markup=back_admin_kb("adm_back_cats"),
        )
        await callback.answer()
    except Exception as exc:
        logger.error("cb_edit_category_emoji error: %s", exc, exc_info=True)
        await callback.answer("❌ Xatolik", show_alert=True)

@router.message(EditCategory.value)
async def process_edit_category_value(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        data = await state.get_data()
        cat_id = data.get("edit_category_id")
        field = data.get("edit_field", "name")
        value = message.text.strip()

        if not value:
            await message.answer("❌ Qiymat bo'sh bo'lishi mumkin emas. Qayta kiriting:")
            return

        update_data = {field: value}
        category = await update_category(session, cat_id, **update_data)
        await state.set_state(None)
        await state.update_data(admin_authenticated=True) # preserve auth state

        if category:
            emoji = category.emoji if category.emoji else "📁"
            logger.info("Category updated: id=%s field=%s", cat_id, field)
            await message.answer(f"✅ Kategoriya yangilandi!\n\n{emoji} <b>{category.name}</b>")
        else:
            await message.answer("❌ Kategoriya topilmadi.")

        # Show updated list
        categories = await get_categories(session)
        await message.answer(
            "📂 <b>Kategoriyalar:</b>",
            reply_markup=admin_categories_kb(categories),
        )
    except Exception as exc:
        logger.error("process_edit_category_value error: %s", exc, exc_info=True)
        await state.clear()
        await message.answer("❌ Kategoriyani yangilashda xatolik.")

# ── Delete category ──────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("adm_cat_del:"))
async def cb_delete_category_confirm(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    logger.info("🎯 Triggered callback: adm_cat_del")
    if not await _is_admin(callback, state):
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    try:
        cat_id = int(callback.data.split(":")[1])
        category = await get_category(session, cat_id)
        if not category:
            await callback.answer("❌ Kategoriya topilmadi", show_alert=True)
            return

        emoji = category.emoji if category.emoji else "📁"
        await callback.message.edit_text(
            f"⚠️ <b>Kategoriyani o'chirish</b>\n\n"
            f"{emoji} <b>{category.name}</b>\n\n"
            f"Haqiqatan ham o'chirmoqchimisiz?\n"
            f"⚠️ Kategoriya ichidagi barcha tovarlar ham o'chiriladi!",
            reply_markup=confirm_kb(f"adm_cat_del_confirm:{cat_id}"),
        )
        await callback.answer()
    except Exception as exc:
        logger.error("cb_delete_category_confirm error: %s", exc, exc_info=True)
        await callback.answer("❌ Xatolik", show_alert=True)

@router.callback_query(F.data.regexp(r"^adm_cat_del_confirm:\d+_yes$"))
async def cb_delete_category_yes(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    logger.info("🎯 Triggered callback: adm_cat_del_confirm_yes")
    if not await _is_admin(callback, state):
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    try:
        parts = callback.data.replace("adm_cat_del_confirm:", "").replace("_yes", "")
        cat_id = int(parts)

        success = await delete_category(session, cat_id)
        if success:
            logger.info("Category deleted: id=%s", cat_id)
            await callback.answer("✅ Kategoriya o'chirildi")
        else:
            await callback.answer("❌ Kategoriya topilmadi", show_alert=True)

        await _show_categories(callback, state, session)
    except Exception as exc:
        logger.error("cb_delete_category_yes error: %s", exc, exc_info=True)
        await callback.answer("❌ Xatolik", show_alert=True)

@router.callback_query(F.data.regexp(r"^adm_cat_del_confirm:\d+_no$"))
async def cb_delete_category_no(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    logger.info("🎯 Triggered callback: adm_cat_del_confirm_no")
    await callback.answer("🚫 Bekor qilindi")
    await _show_categories(callback, state, session)

# ── Back to categories list ──────────────────────────────────────────────
@router.callback_query(F.data == "adm_back_cats")
async def cb_back_to_categories(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    logger.info("🎯 Triggered callback: adm_back_cats")
    if not await _is_admin(callback, state):
        await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    await state.clear()
    await state.update_data(admin_authenticated=True) # preserve auth state
    await _show_categories(callback, state, session)
