from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from utils.helpers import format_price, format_order_status

def admin_menu_kb() -> InlineKeyboardMarkup:
    """Generate admin dashboard main menu as Inline Keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📂 Categories", callback_data="admin_categories"),
                InlineKeyboardButton(text="📦 Products", callback_data="admin_products")
            ],
            [
                InlineKeyboardButton(text="🛒 Orders", callback_data="admin_orders"),
                InlineKeyboardButton(text="📊 Statistics", callback_data="admin_statistics")
            ],
            [
                InlineKeyboardButton(text="⚙️ Settings", callback_data="admin_settings"),
                InlineKeyboardButton(text="📖 Instruktsiya", callback_data="admin_instruction")
            ],
            [
                InlineKeyboardButton(text="🚪 Exit", callback_data="admin_exit")
            ]
        ]
    )

def admin_categories_kb(categories: list) -> InlineKeyboardMarkup:
    """Generate keyboard for categories listing in admin dashboard."""
    keyboard = []
    
    for cat in categories:
        emoji = cat.emoji if cat.emoji else "📁"
        keyboard.append([
            InlineKeyboardButton(text=f"{emoji} {cat.name}", callback_data=f"adm_cat_view:{cat.id}"),
            InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"adm_cat_edit:{cat.id}"),
            InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"adm_cat_del:{cat.id}"),
        ])
        
    keyboard.append([InlineKeyboardButton(text="➕ Yangi kategoriya", callback_data="adm_cat_add")])
    keyboard.append([InlineKeyboardButton(text="🔙 Bosh menyu", callback_data="adm_back")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def admin_category_edit_kb(category_id: int) -> InlineKeyboardMarkup:
    """Generate keyboard for modifying a single category's fields."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📝 Nomini o'zgartirish", callback_data=f"adm_cat_edit_name:{category_id}"),
                InlineKeyboardButton(text="😀 Emojini o'zgartirish", callback_data=f"adm_cat_edit_emoji:{category_id}"),
            ],
            [
                InlineKeyboardButton(text="🔙 Orqaga", callback_data="adm_back_cats")
            ]
        ]
    )

def admin_products_kb(products: list, page: int = 0, total_pages: int = 1) -> InlineKeyboardMarkup:
    """Generate keyboard for listing products with pagination in admin."""
    keyboard = []
    
    for prod in products:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{prod.name} - {format_price(prod.price)}",
                callback_data=f"adm_prod_view:{prod.id}"
            )
        ])
        
    pagination_row = []
    if page > 0:
        pagination_row.append(InlineKeyboardButton(text="◀️", callback_data=f"adm_prod_page:{page-1}"))
    if total_pages > 1:
        pagination_row.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="ignore"))
    if page < total_pages - 1:
        pagination_row.append(InlineKeyboardButton(text="▶️", callback_data=f"adm_prod_page:{page+1}"))
        
    if pagination_row:
        keyboard.append(pagination_row)
        
    keyboard.append([
        InlineKeyboardButton(text="➕ Yangi tovar", callback_data="adm_prod_add"),
        InlineKeyboardButton(text="🔍 Qidirish", callback_data="adm_prod_search"),
    ])
    keyboard.append([InlineKeyboardButton(text="🔙 Bosh menyu", callback_data="adm_back")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def admin_product_actions_kb(product_id: int) -> InlineKeyboardMarkup:
    """Generate keyboard for single product detail view actions."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"adm_prod_edit:{product_id}"),
                InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"adm_prod_del:{product_id}"),
            ],
            [
                InlineKeyboardButton(text="🔙 Orqaga", callback_data="adm_back_prods")
            ]
        ]
    )

def admin_product_edit_kb(product_id: int) -> InlineKeyboardMarkup:
    """Generate keyboard containing edit triggers for product fields."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📝 Nomi", callback_data=f"adm_prod_edit_name:{product_id}"),
                InlineKeyboardButton(text="📄 Tavsifi", callback_data=f"adm_prod_edit_desc:{product_id}"),
            ],
            [
                InlineKeyboardButton(text="💰 Narxi", callback_data=f"adm_prod_edit_price:{product_id}"),
                InlineKeyboardButton(text="📦 Ombordagi soni", callback_data=f"adm_prod_edit_stock:{product_id}"),
            ],
            [
                InlineKeyboardButton(text="📷 Rasm yuklash", callback_data=f"adm_prod_edit_photo:{product_id}"),
            ],
            [
                InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"adm_prod_view:{product_id}")
            ]
        ]
    )

def order_status_kb(order_id: int) -> InlineKeyboardMarkup:
    """Generate keyboard containing status modification buttons for orders."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"adm_ord_status:{order_id}:accepted"),
                InlineKeyboardButton(text="🚚 Yetkazishda", callback_data=f"adm_ord_status:{order_id}:delivering"),
            ],
            [
                InlineKeyboardButton(text="🏁 Bajarildi", callback_data=f"adm_ord_status:{order_id}:completed"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"adm_ord_status:{order_id}:canceled"),
            ]
        ]
    )

def admin_orders_kb(orders: list, page: int = 0, total_pages: int = 1) -> InlineKeyboardMarkup:
    """Generate keyboard listing orders with status and pagination."""
    keyboard = []
    
    for order in orders:
        status_text = format_order_status(order.status)
        keyboard.append([
            InlineKeyboardButton(
                text=f"#{order.id} | {status_text} | {format_price(order.total)}",
                callback_data=f"adm_ord_view:{order.id}"
            )
        ])
        
    pagination_row = []
    if page > 0:
        pagination_row.append(InlineKeyboardButton(text="◀️", callback_data=f"adm_ord_page:{page-1}"))
    if total_pages > 1:
        pagination_row.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="ignore"))
    if page < total_pages - 1:
        pagination_row.append(InlineKeyboardButton(text="▶️", callback_data=f"adm_ord_page:{page+1}"))
        
    if pagination_row:
        keyboard.append(pagination_row)
        
    keyboard.append([InlineKeyboardButton(text="🔙 Bosh menyu", callback_data="adm_back")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def admin_settings_kb() -> InlineKeyboardMarkup:
    """Generate settings dashboard buttons."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🚚 Yetkazish narxi", callback_data="adm_set_delivery"),
                InlineKeyboardButton(text="💳 To'lov turlari", callback_data="adm_set_payment"),
            ],
            [
                InlineKeyboardButton(text="👥 Adminlar ro'yxati", callback_data="adm_set_admins"),
                InlineKeyboardButton(text="📢 Xabar yuborish", callback_data="adm_broadcast"),
            ],
            [
                InlineKeyboardButton(text="🔙 Bosh menyu", callback_data="adm_back")
            ]
        ]
    )

def confirm_kb(prefix: str = "") -> InlineKeyboardMarkup:
    """Generate reusable yes/no confirmation buttons."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha", callback_data=f"{prefix}_yes"),
                InlineKeyboardButton(text="❌ Yo'q", callback_data=f"{prefix}_no"),
            ]
        ]
    )

def back_admin_kb(callback: str = "adm_back") -> InlineKeyboardMarkup:
    """Generate back button using a target callback."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data=callback)]
        ]
    )

def admin_select_category_kb(categories: list) -> InlineKeyboardMarkup:
    """Generate keyboard for selecting a category to view/manage its products."""
    keyboard = []
    
    for cat in categories:
        emoji = cat.emoji if cat.emoji else "📁"
        keyboard.append([
            InlineKeyboardButton(text=f"{emoji} {cat.name}", callback_data=f"adm_cat_products:{cat.id}")
        ])
        
    keyboard.append([
        InlineKeyboardButton(text="➕ Yangi tovar", callback_data="adm_prod_add"),
        InlineKeyboardButton(text="🔍 Qidirish", callback_data="adm_prod_search"),
    ])
    keyboard.append([InlineKeyboardButton(text="🔙 Bosh menyu", callback_data="adm_back")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def admin_select_category_for_add_kb(categories: list) -> InlineKeyboardMarkup:
    """Generate keyboard for selecting a category when creating a new product."""
    keyboard = []
    
    for cat in categories:
        emoji = cat.emoji if cat.emoji else "📁"
        keyboard.append([
            InlineKeyboardButton(text=f"{emoji} {cat.name}", callback_data=f"adm_cat_view:{cat.id}")
        ])
        
    keyboard.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="adm_back_prods")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def admin_category_products_kb(products: list, category_id: int, page: int = 0, total_pages: int = 1) -> InlineKeyboardMarkup:
    """Generate keyboard for listing products of a specific category with pagination in admin."""
    keyboard = []
    
    for prod in products:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{prod.name} - {format_price(prod.price)}",
                callback_data=f"adm_prod_view:{prod.id}"
            )
        ])
        
    pagination_row = []
    if page > 0:
        pagination_row.append(InlineKeyboardButton(text="◀️", callback_data=f"adm_cat_prod_page:{category_id}:{page-1}"))
    if total_pages > 1:
        pagination_row.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="ignore"))
    if page < total_pages - 1:
        pagination_row.append(InlineKeyboardButton(text="▶️", callback_data=f"adm_cat_prod_page:{category_id}:{page+1}"))
        
    if pagination_row:
        keyboard.append(pagination_row)
        
    keyboard.append([
        InlineKeyboardButton(text="➕ Yangi tovar", callback_data=f"adm_prod_add_to_cat:{category_id}"),
        InlineKeyboardButton(text="🔍 Qidirish", callback_data="adm_prod_search"),
    ])
    keyboard.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="adm_back_prods")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

