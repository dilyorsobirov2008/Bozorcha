"""
Admin category management handlers.
CRUD operations for product categories.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from locales import get_text
from keyboards.reply import admin_menu_keyboard, admin_categories_keyboard
from keyboards.inline import (
    category_admin_inline_keyboard,
    confirm_delete_keyboard,
    category_select_keyboard,
)
from states.admin_states import AdminStates
from services.category_service import CategoryService

router = Router(name="admin_categories")


# ──────────────────────────────────────────────────────────
# Categories menu
# ──────────────────────────────────────────────────────────
@router.message(
    AdminStates.in_admin_menu,
    F.text.in_({"📂 Kategoriyalar", "📂 Категории"}),
)
async def categories_menu(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    await message.answer(
        get_text(lang, "admin_categories_menu"),
        reply_markup=admin_categories_keyboard(lang),
    )
    await state.set_state(AdminStates.in_categories_menu)


# ──────────────────────────────────────────────────────────
# Add category flow
# ──────────────────────────────────────────────────────────
@router.message(
    AdminStates.in_categories_menu,
    F.text.in_({"➕ Qo'shish", "➕ Добавить"}),
)
async def add_category_start(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    await message.answer(get_text(lang, "enter_category_name"))
    await state.set_state(AdminStates.adding_category_name)


@router.message(AdminStates.adding_category_name, F.text)
async def add_category_name(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    await state.update_data(new_cat_name=message.text.strip())
    await message.answer(
        get_text(lang, "send_category_image"),
    )
    await state.set_state(AdminStates.adding_category_image)


@router.message(AdminStates.adding_category_image, F.photo)
async def add_category_image(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    photo_id = message.photo[-1].file_id  # Largest resolution

    name = data.get("new_cat_name", "")
    await CategoryService.create(session, name=name, image=photo_id)

    await message.answer(
        get_text(lang, "category_added").format(name=name),
        reply_markup=admin_categories_keyboard(lang),
    )
    await state.set_state(AdminStates.in_categories_menu)


@router.message(
    AdminStates.adding_category_image,
    F.text.in_({"/skip", "skip", "⏩ O'tkazish", "⏩ Пропустить"}),
)
async def add_category_skip_image(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    name = data.get("new_cat_name", "")

    await CategoryService.create(session, name=name, image=None)

    await message.answer(
        get_text(lang, "category_added").format(name=name),
        reply_markup=admin_categories_keyboard(lang),
    )
    await state.set_state(AdminStates.in_categories_menu)


# ──────────────────────────────────────────────────────────
# List categories
# ──────────────────────────────────────────────────────────
@router.message(
    AdminStates.in_categories_menu,
    F.text.in_({"📋 Ro'yxat", "📋 Список"}),
)
async def list_categories(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    categories = await CategoryService.get_all(session)
    if not categories:
        await message.answer(get_text(lang, "no_categories"))
        return

    await message.answer(
        get_text(lang, "category_list"),
        reply_markup=category_admin_inline_keyboard(categories, lang),
    )


# ──────────────────────────────────────────────────────────
# Edit category
# ──────────────────────────────────────────────────────────
@router.message(
    AdminStates.in_categories_menu,
    F.text.in_({"✏️ Tahrirlash", "✏️ Редактировать"}),
)
async def edit_category_start(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    categories = await CategoryService.get_all(session)
    if not categories:
        await message.answer(get_text(lang, "no_categories"))
        return

    await message.answer(
        get_text(lang, "select_category_edit"),
        reply_markup=category_admin_inline_keyboard(categories, lang, prefix="edit_cat_"),
    )
    await state.set_state(AdminStates.selecting_category_edit)


@router.callback_query(
    AdminStates.selecting_category_edit,
    F.data.startswith("edit_cat_"),
)
async def edit_category_selected(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    category_id = int(callback.data.split("_")[-1])

    await state.update_data(edit_cat_id=category_id)
    await callback.message.edit_text(get_text(lang, "enter_new_category_name"))
    await state.set_state(AdminStates.editing_category_name)
    await callback.answer()


@router.message(AdminStates.editing_category_name, F.text)
async def edit_category_name_entered(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    category_id = data.get("edit_cat_id")
    new_name = message.text.strip()

    await CategoryService.update(session, category_id, name=new_name)

    await message.answer(
        get_text(lang, "category_updated").format(name=new_name),
        reply_markup=admin_categories_keyboard(lang),
    )
    await state.set_state(AdminStates.in_categories_menu)


# ──────────────────────────────────────────────────────────
# Delete category
# ──────────────────────────────────────────────────────────
@router.message(
    AdminStates.in_categories_menu,
    F.text.in_({"🗑 O'chirish", "🗑 Удалить"}),
)
async def delete_category_start(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    categories = await CategoryService.get_all(session)
    if not categories:
        await message.answer(get_text(lang, "no_categories"))
        return

    await message.answer(
        get_text(lang, "select_category_delete"),
        reply_markup=category_admin_inline_keyboard(categories, lang, prefix="del_cat_"),
    )
    await state.set_state(AdminStates.selecting_category_delete)


@router.callback_query(
    AdminStates.selecting_category_delete,
    F.data.startswith("del_cat_"),
)
async def delete_category_selected(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    category_id = int(callback.data.split("_")[-1])

    await state.update_data(del_cat_id=category_id)
    category = await CategoryService.get_by_id(session, category_id)

    await callback.message.edit_text(
        get_text(lang, "confirm_delete_category").format(name=category.name),
        reply_markup=confirm_delete_keyboard(lang, prefix="confirm_del_cat"),
    )
    await callback.answer()


@router.callback_query(
    AdminStates.selecting_category_delete,
    F.data == "confirm_del_cat_yes",
)
async def delete_category_confirmed(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    category_id = data.get("del_cat_id")

    await CategoryService.delete(session, category_id)

    await callback.message.edit_text(get_text(lang, "category_deleted"))
    await callback.message.answer(
        get_text(lang, "admin_categories_menu"),
        reply_markup=admin_categories_keyboard(lang),
    )
    await state.set_state(AdminStates.in_categories_menu)
    await callback.answer()


@router.callback_query(
    AdminStates.selecting_category_delete,
    F.data == "confirm_del_cat_no",
)
async def delete_category_cancelled(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    await callback.message.edit_text(get_text(lang, "action_cancelled"))
    await state.set_state(AdminStates.in_categories_menu)
    await callback.answer()


# ──────────────────────────────────────────────────────────
# Back to admin menu
# ──────────────────────────────────────────────────────────
@router.message(
    AdminStates.in_categories_menu,
    F.text.in_({"⬅️ Ortga", "⬅️ Назад"}),
)
async def back_to_admin_menu(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    await message.answer(
        get_text(lang, "admin_menu"),
        reply_markup=admin_menu_keyboard(lang),
    )
    await state.set_state(AdminStates.in_admin_menu)
