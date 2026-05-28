from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from locales import get_text


def product_keyboard(
    lang: str, product_id: int, quantity: int = 1
) -> InlineKeyboardMarkup:
    """Product detail keyboard with quantity controls and add-to-cart."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➖", callback_data=f"minus_{product_id}"
                ),
                InlineKeyboardButton(
                    text=str(quantity), callback_data="noop"
                ),
                InlineKeyboardButton(
                    text="➕", callback_data=f"plus_{product_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=get_text(lang, "add_to_cart"),
                    callback_data=f"add_cart_{product_id}_{quantity}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=get_text(lang, "back"),
                    callback_data="back_to_products",
                )
            ],
        ]
    )


def cart_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Cart actions keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_text(lang, "order_btn"),
                    callback_data="checkout",
                )
            ],
            [
                InlineKeyboardButton(
                    text=get_text(lang, "clear_cart"),
                    callback_data="clear_cart",
                )
            ],
            [
                InlineKeyboardButton(
                    text=get_text(lang, "back"),
                    callback_data="back_to_menu",
                )
            ],
        ]
    )


def payment_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Payment method selection keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_text(lang, "cash"),
                    callback_data="pay_cash",
                )
            ],
            [
                InlineKeyboardButton(
                    text=get_text(lang, "click_pay"),
                    callback_data="pay_click",
                )
            ],
            [
                InlineKeyboardButton(
                    text=get_text(lang, "payme_pay"),
                    callback_data="pay_payme",
                )
            ],
        ]
    )


def order_admin_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """Admin order action keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Qabul",
                    callback_data=f"accept_{order_id}",
                ),
                InlineKeyboardButton(
                    text="🚚",
                    callback_data=f"ship_{order_id}",
                ),
                InlineKeyboardButton(
                    text="❌",
                    callback_data=f"cancel_order_{order_id}",
                ),
            ]
        ]
    )


def pagination_keyboard(
    prefix: str, current_page: int, total_pages: int
) -> InlineKeyboardMarkup:
    """Pagination keyboard. Hides left/right at boundaries."""
    buttons: list[InlineKeyboardButton] = []

    if current_page > 1:
        buttons.append(
            InlineKeyboardButton(
                text="⬅️",
                callback_data=f"{prefix}_page_{current_page - 1}",
            )
        )

    buttons.append(
        InlineKeyboardButton(
            text=f"{current_page}/{total_pages}",
            callback_data="noop",
        )
    )

    if current_page < total_pages:
        buttons.append(
            InlineKeyboardButton(
                text="➡️",
                callback_data=f"{prefix}_page_{current_page + 1}",
            )
        )

    return InlineKeyboardMarkup(inline_keyboard=[buttons])


def confirm_delete_keyboard(
    lang: str, prefix: str, item_id: int
) -> InlineKeyboardMarkup:
    """Confirmation keyboard for delete operations."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_text(lang, "yes_delete"),
                    callback_data=f"{prefix}_confirm_del_{item_id}",
                ),
                InlineKeyboardButton(
                    text=get_text(lang, "no_cancel"),
                    callback_data=f"{prefix}_cancel_del",
                ),
            ]
        ]
    )


def category_select_keyboard(
    categories: list, lang: str
) -> InlineKeyboardMarkup:
    """Keyboard to select a category (one button per category)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=cat.name,
                    callback_data=f"select_cat_{cat.id}",
                )
            ]
            for cat in categories
        ]
    )


def product_list_inline_keyboard(
    products: list, lang: str
) -> InlineKeyboardMarkup:
    """Keyboard listing products (one button per product)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=prod.name,
                    callback_data=f"view_prod_{prod.id}",
                )
            ]
            for prod in products
        ]
    )


def product_admin_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Admin product actions keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️",
                    callback_data=f"edit_prod_{product_id}",
                ),
                InlineKeyboardButton(
                    text="💰",
                    callback_data=f"price_prod_{product_id}",
                ),
                InlineKeyboardButton(
                    text="📦",
                    callback_data=f"stock_prod_{product_id}",
                ),
                InlineKeyboardButton(
                    text="🗑",
                    callback_data=f"del_prod_{product_id}",
                ),
            ]
        ]
    )


def category_admin_inline_keyboard(categories: list) -> InlineKeyboardMarkup:
    """Admin category selection keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=cat.name,
                    callback_data=f"admin_cat_{cat.id}",
                )
            ]
            for cat in categories
        ]
    )


def order_list_inline_keyboard(orders: list) -> InlineKeyboardMarkup:
    """Keyboard listing orders for admin review."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"#{order.id} - {order.created_at:%Y-%m-%d %H:%M}",
                    callback_data=f"view_order_{order.id}",
                )
            ]
            for order in orders
        ]
    )
