from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from utils.helpers import format_price

def main_menu_kb() -> ReplyKeyboardMarkup:
    """Generate main reply keyboard for user."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Harid qilish")],
            [KeyboardButton(text="🔐 Admin Panel")],
        ],
        resize_keyboard=True,
    )

def categories_kb(categories: list, page: int = 0, per_page: int = 8) -> InlineKeyboardMarkup:
    """Generate inline keyboard for categories list with pagination."""
    keyboard = []
    
    total_pages = (len(categories) + per_page - 1) // per_page if categories else 1
    page = max(0, min(page, total_pages - 1))
    
    start_idx = page * per_page
    end_idx = start_idx + per_page
    page_items = categories[start_idx:end_idx]
    
    for cat in page_items:
        emoji = cat.emoji if cat.emoji else "📁"
        keyboard.append([
            InlineKeyboardButton(
                text=f"{emoji} {cat.name}",
                callback_data=f"cat:{cat.id}"
            )
        ])
        
    pagination_row = []
    if page > 0:
        pagination_row.append(InlineKeyboardButton(text="◀️ Oldingi", callback_data=f"page_cat:{page-1}"))
    if total_pages > 1:
        pagination_row.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="ignore"))
    if page < total_pages - 1:
        pagination_row.append(InlineKeyboardButton(text="Keyingi ▶️", callback_data=f"page_cat:{page+1}"))
        
    if pagination_row:
        keyboard.append(pagination_row)
        
    keyboard.append([InlineKeyboardButton(text="🔙 Bosh menyu", callback_data="back_to_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def products_kb(products: list, category_id: int, page: int = 0, per_page: int = 5) -> InlineKeyboardMarkup:
    """Generate inline keyboard for products within a category."""
    keyboard = []
    
    total_pages = (len(products) + per_page - 1) // per_page if products else 1
    page = max(0, min(page, total_pages - 1))
    
    start_idx = page * per_page
    end_idx = start_idx + per_page
    page_items = products[start_idx:end_idx]
    
    for prod in page_items:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{prod.name} - {format_price(prod.price)}",
                callback_data=f"prod:{prod.id}"
            )
        ])
        
    pagination_row = []
    if page > 0:
        pagination_row.append(InlineKeyboardButton(text="◀️ Oldingi", callback_data=f"page_prod:{category_id}:{page-1}"))
    if total_pages > 1:
        pagination_row.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="ignore"))
    if page < total_pages - 1:
        pagination_row.append(InlineKeyboardButton(text="Keyingi ▶️", callback_data=f"page_prod:{category_id}:{page+1}"))
        
    if pagination_row:
        keyboard.append(pagination_row)
        
    keyboard.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_cats")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def product_card_kb(product_id: int, quantity: int = 1) -> InlineKeyboardMarkup:
    """Generate keyboard for a single product card detailing controls and add to cart."""
    keyboard = [
        [
            InlineKeyboardButton(text="➖", callback_data=f"qty:{product_id}:minus"),
            InlineKeyboardButton(text=f"{quantity}", callback_data=f"qty:{product_id}:current"),
            InlineKeyboardButton(text="➕", callback_data=f"qty:{product_id}:plus"),
        ],
        [
            InlineKeyboardButton(
                text="🛒 Savatchaga qo'shish",
                callback_data=f"add_cart:{product_id}:{quantity}"
            )
        ],
        [
            InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_prods")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def cart_kb(cart_items: list) -> InlineKeyboardMarkup:
    """Generate keyboard for shopping cart containing items and quantity controls."""
    keyboard = []
    
    for item in cart_items:
        prod = item.product
        keyboard.append([
            InlineKeyboardButton(
                text=f"{prod.name} ({item.quantity} dona)",
                callback_data=f"prod:{prod.id}"
            )
        ])
        keyboard.append([
            InlineKeyboardButton(text="➖", callback_data=f"cart_qty:{item.id}:minus"),
            InlineKeyboardButton(text="➕", callback_data=f"cart_qty:{item.id}:plus"),
            InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"cart_del:{item.id}"),
        ])
        
    if cart_items:
        keyboard.append([
            InlineKeyboardButton(text="🗑 Savatchani tozalash", callback_data="cart_clear"),
            InlineKeyboardButton(text="📦 Buyurtma berish", callback_data="checkout"),
        ])
        
    keyboard.append([
        InlineKeyboardButton(text="🛒 Haridni davom ettirish", callback_data="back_to_cats")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def payment_kb(toggles: dict = None) -> InlineKeyboardMarkup:
    """Generate keyboard for selecting payment type."""
    keyboard = []
    row = []
    
    if toggles is None:
        toggles = {"cash": True, "click": True, "payme": True}
        
    if toggles.get("cash", True):
        row.append(InlineKeyboardButton(text="💵 Naqd", callback_data="pay:cash"))
    if toggles.get("click", True):
        row.append(InlineKeyboardButton(text="📱 Click", callback_data="pay:click"))
    if toggles.get("payme", True):
        row.append(InlineKeyboardButton(text="📱 Payme", callback_data="pay:payme"))
        
    if row:
        keyboard.append(row)
        
    keyboard.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_cart")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def confirm_order_kb() -> InlineKeyboardMarkup:
    """Generate checkout confirmation keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="order_confirm"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="order_cancel"),
            ]
        ]
    )

def phone_kb() -> ReplyKeyboardMarkup:
    """Generate keyboard requesting user contact."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📞 Telefon raqamni yuborish", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
