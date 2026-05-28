from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from locales import get_text
from keyboards.reply import admin_menu_keyboard, admin_settings_keyboard
from states.admin_states import AdminStates
from services.admin_service import AdminService
from config.settings import settings

router = Router(name="admin_settings")


# ──────────────────────────────────────────────────────────
# Settings Menu
# ──────────────────────────────────────────────────────────
@router.message(
    AdminStates.in_admin_menu,
    F.text.in_({"⚙️ Sozlamalar", "⚙️ Настройки"}),
)
async def settings_menu(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    await message.answer(
        get_text(lang, "admin_settings"),
        reply_markup=admin_settings_keyboard(lang),
    )


# ──────────────────────────────────────────────────────────
# Payment Settings
# ──────────────────────────────────────────────────────────
@router.message(
    AdminStates.in_admin_menu,
    F.text.in_({"💳 To'lov sozlamalari", "💳 Настройки оплаты"}),
)
async def payment_settings_view(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    info = (
        "💳 <b>Click</b>: ✅ Active\n"
        "💳 <b>Payme</b>: ✅ Active\n"
        "💵 <b>Cash</b>: ✅ Active\n\n"
        "To modify API integrations, please edit your <code>.env</code> file."
    )
    await message.answer(info)


# ──────────────────────────────────────────────────────────
# Delivery Area
# ──────────────────────────────────────────────────────────
@router.message(
    AdminStates.in_admin_menu,
    F.text.in_({"📍 Dostavka hududi", "📍 Зона доставки"}),
)
async def delivery_area_view(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    info = (
        "📍 <b>Dostavka hududi / Зона доставки</b>:\n\n"
        "Toshkent shahri barcha tumanlari / Вся территория города Ташкент."
    )
    await message.answer(info)


# ──────────────────────────────────────────────────────────
# Delivery Price
# ──────────────────────────────────────────────────────────
@router.message(
    AdminStates.in_admin_menu,
    F.text.in_({"🚚 Dostavka narxi", "🚚 Стоимость доставки"}),
)
async def delivery_price_start(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    current_price = settings.DELIVERY_PRICE
    await message.answer(
        f"💰 Hozirgi dostavka narxi: <b>{current_price:,} so'm</b>\n"
        f"Текущая стоимость доставки: <b>{current_price:,} сум</b>\n\n"
        + get_text(lang, "enter_delivery_price")
    )
    await state.set_state(AdminStates.entering_delivery_price)


@router.message(AdminStates.entering_delivery_price, F.text)
async def delivery_price_entered(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    text = message.text.strip()

    try:
        new_price = int(text)
        if new_price < 0:
            raise ValueError()
    except ValueError:
        await message.answer("❌ Iltimos, musbat son kiriting!\nПожалуйста, введите положительное число!")
        return

    settings.DELIVERY_PRICE = new_price
    await message.answer(
        get_text(lang, "delivery_price_updated").format(price=f"{new_price:,}"),
        reply_markup=admin_settings_keyboard(lang),
    )
    await state.set_state(AdminStates.in_admin_menu)


# ──────────────────────────────────────────────────────────
# Admin Management (Admins list & CRUD)
# ──────────────────────────────────────────────────────────
def _get_admins_markup(admins: list, lang: str) -> InlineKeyboardMarkup:
    buttons = []
    for admin in admins:
        buttons.append([
            InlineKeyboardButton(text=f"👤 {admin.login}", callback_data="noop"),
            InlineKeyboardButton(text="🗑", callback_data=f"del_adm_{admin.id}"),
        ])
    buttons.append([
        InlineKeyboardButton(text=get_text(lang, "add_admin"), callback_data="add_new_admin")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(
    AdminStates.in_admin_menu,
    F.text.in_({"👨‍💼 Adminlar", "👨‍💼 Администраторы"}),
)
async def manage_admins_start(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    admins = await AdminService.get_all(session)
    await message.answer(
        "👨‍💼 Tizim administratorlari / Администраторы системы:",
        reply_markup=_get_admins_markup(admins, lang),
    )


@router.callback_query(
    AdminStates.in_admin_menu,
    F.data.startswith("del_adm_"),
)
async def delete_admin_click(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    admin_id = int(callback.data.split("_")[-1])

    # Prevent deleting self if possible (we don't strictly enforce, but we can do it)
    current_admin_id = data.get("admin_id")
    if current_admin_id == admin_id:
        await callback.answer("❌ O'zingizni o'chira olmaysiz! / Вы не можете удалить себя!", show_alert=True)
        return

    success = await AdminService.delete(session, admin_id)
    if success:
        await callback.answer(get_text(lang, "admin_deleted"))
    else:
        await callback.answer("❌ Xatolik yuz berdi / Ошибка!", show_alert=True)

    admins = await AdminService.get_all(session)
    await callback.message.edit_reply_markup(reply_markup=_get_admins_markup(admins, lang))


@router.callback_query(
    AdminStates.in_admin_menu,
    F.data == "add_new_admin",
)
async def add_admin_click(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    await callback.message.answer(get_text(lang, "enter_admin_login"))
    await state.set_state(AdminStates.adding_admin_login)
    await callback.answer()


@router.message(AdminStates.adding_admin_login, F.text)
async def admin_login_entered(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    await state.update_data(new_adm_login=message.text.strip())
    await message.answer(get_text(lang, "enter_admin_password"))
    await state.set_state(AdminStates.adding_admin_password)


@router.message(AdminStates.adding_admin_password, F.text)
async def admin_password_entered(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    password = message.text.strip()
    login = data.get("new_adm_login", "")

    try:
        await AdminService.create(session, login=login, password=password)
        await message.answer(
            get_text(lang, "admin_added"),
            reply_markup=admin_settings_keyboard(lang),
        )
    except Exception as e:
        await message.answer(
            f"❌ Xatolik (ehtimol bunday login mavjud): {str(e)}",
            reply_markup=admin_settings_keyboard(lang),
        )

    await state.set_state(AdminStates.in_admin_menu)


# ──────────────────────────────────────────────────────────
# Back button
# ──────────────────────────────────────────────────────────
@router.message(
    AdminStates.in_admin_menu,
    F.text.in_({"⬅️ Ortga", "⬅️ Назад"}),
)
async def back_to_admin_menu(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    # In settings we might be in in_admin_menu state.
    # Going back to admin main menu is simple.
    await message.answer(
        get_text(lang, "admin_menu_title"),
        reply_markup=admin_menu_keyboard(lang),
    )
