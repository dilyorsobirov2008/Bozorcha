from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from locales import get_text


def language_keyboard() -> ReplyKeyboardMarkup:
    """Language selection keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🇺🇿 O'zbekcha"),
                KeyboardButton(text="🇷🇺 Русский"),
            ]
        ],
        resize_keyboard=True,
    )


def main_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """Main menu keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_text(lang, "shopping"))],
            [KeyboardButton(text=get_text(lang, "admin_panel"))],
        ],
        resize_keyboard=True,
    )


def categories_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """Categories keyboard with 6 category buttons and a back button."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=get_text(lang, "drinks")),
                KeyboardButton(text=get_text(lang, "sweets")),
            ],
            [
                KeyboardButton(text=get_text(lang, "meat")),
                KeyboardButton(text=get_text(lang, "dairy")),
            ],
            [
                KeyboardButton(text=get_text(lang, "vegetables")),
                KeyboardButton(text=get_text(lang, "household")),
            ],
            [KeyboardButton(text=get_text(lang, "back"))],
        ],
        resize_keyboard=True,
    )


def admin_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """Admin panel main menu keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=get_text(lang, "categories")),
                KeyboardButton(text=get_text(lang, "products")),
            ],
            [
                KeyboardButton(text=get_text(lang, "orders")),
                KeyboardButton(text=get_text(lang, "statistics")),
            ],
            [
                KeyboardButton(text=get_text(lang, "settings")),
                KeyboardButton(text=get_text(lang, "logout")),
            ],
        ],
        resize_keyboard=True,
    )


def admin_categories_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """Admin categories management keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=get_text(lang, "add_category")),
                KeyboardButton(text=get_text(lang, "category_list")),
            ],
            [
                KeyboardButton(text=get_text(lang, "edit_category")),
                KeyboardButton(text=get_text(lang, "delete_category")),
            ],
            [KeyboardButton(text=get_text(lang, "back"))],
        ],
        resize_keyboard=True,
    )


def admin_products_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """Admin products management keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=get_text(lang, "add_product")),
                KeyboardButton(text=get_text(lang, "product_list")),
            ],
            [
                KeyboardButton(text=get_text(lang, "edit_product")),
                KeyboardButton(text=get_text(lang, "change_price")),
            ],
            [
                KeyboardButton(text=get_text(lang, "change_stock")),
                KeyboardButton(text=get_text(lang, "delete_product")),
            ],
            [KeyboardButton(text=get_text(lang, "search"))],
            [KeyboardButton(text=get_text(lang, "back"))],
        ],
        resize_keyboard=True,
    )


def admin_orders_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """Admin orders management keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=get_text(lang, "new_orders")),
                KeyboardButton(text=get_text(lang, "delivering")),
            ],
            [
                KeyboardButton(text=get_text(lang, "completed")),
                KeyboardButton(text=get_text(lang, "cancelled")),
            ],
            [KeyboardButton(text=get_text(lang, "search"))],
            [KeyboardButton(text=get_text(lang, "back"))],
        ],
        resize_keyboard=True,
    )


def admin_settings_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """Admin settings keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=get_text(lang, "payment_settings")),
                KeyboardButton(text=get_text(lang, "delivery_price_btn")),
            ],
            [
                KeyboardButton(text=get_text(lang, "delivery_area")),
                KeyboardButton(text=get_text(lang, "manage_admins")),
            ],
            [KeyboardButton(text=get_text(lang, "broadcast"))],
            [KeyboardButton(text=get_text(lang, "back"))],
        ],
        resize_keyboard=True,
    )


def phone_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """Phone number sharing keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=get_text(lang, "share_phone"),
                    request_contact=True,
                )
            ],
            [KeyboardButton(text=get_text(lang, "back"))],
        ],
        resize_keyboard=True,
    )
