"""Uzbek language texts for the supermarket bot."""

texts: dict[str, str] = {
    # ── General ─────────────────────────────────────────────────────────
    "welcome": "Assalomu alaykum! 👋\nXush kelibsiz botimizga.",
    "choose_language": "🌐 Tilni tanlang:",
    "lang_uz": "🇺🇿 O'zbekcha",
    "lang_ru": "🇷🇺 Русский",
    "main_menu": "🏠 Asosiy menyu",
    "shopping": "🛒 Harid qilish",
    "admin_panel": "🔐 Admin Panel",

    # ── Categories ──────────────────────────────────────────────────────
    "categories_title": "📂 Kategoriyalarni tanlang:",
    "drinks": "🥤 Ichimliklar",
    "sweets": "🍫 Shirinliklar",
    "meat": "🥩 Go'sht",
    "dairy": "🥛 Sut mahsulotlari",
    "vegetables": "🥦 Sabzavotlar",
    "household": "🧼 Maishiy",
    "back": "⬅️ Ortga",

    # ── Product ─────────────────────────────────────────────────────────
    "product_info": "📦 {name}\n💰 {price} so'm\n📦 Omborda: {stock} ta",
    "in_stock": "📦 Omborda: {stock} ta",
    "add_to_cart": "🛒 Savatchaga qo'shish",

    # ── Cart ────────────────────────────────────────────────────────────
    "cart_title": "🛒 Savatchangiz:",
    "cart_empty": "🛒 Savatcha bo'sh",
    "cart_item": "• {name} x{quantity} = {total} so'm",
    "cart_total": "\n💰 Jami: {total} so'm",
    "clear_cart": "🗑 Tozalash",

    # ── Order ───────────────────────────────────────────────────────────
    "order_btn": "🚚 Buyurtma berish",
    "send_address": "📍 Manzilingizni yuboring (matn yoki lokatsiya):",
    "send_phone": "📞 Telefon raqamingizni yuboring:",
    "share_phone": "📱 Raqamni ulashish",
    "choose_payment": "💳 To'lov turini tanlang:",
    "cash": "💵 Naqd",
    "click_pay": "💳 Click",
    "payme_pay": "💳 Payme",
    "order_confirmed": (
        "✅ Buyurtmangiz qabul qilindi!\n\n"
        "📋 Buyurtma raqami: #{order_id}\n"
        "💰 Jami: {total} so'm\n\n"
        "Tez orada siz bilan bog'lanamiz!"
    ),
    "order_notification": (
        "🆕 Yangi buyurtma #{order_id}\n\n"
        "👤 {name}\n📞 {phone}\n📍 {address}\n\n"
        "🛒 Mahsulotlar:\n{items}\n\n"
        "💰 Jami: {total} so'm\n💳 To'lov: {payment}"
    ),
    "accept_order": "✅ Qabul qilish",
    "shipped_order": "🚚 Yuborildi",
    "cancel_order": "❌ Bekor qilish",

    # ── Admin – Auth ────────────────────────────────────────────────────
    "admin_login": "👤 Login kiriting:",
    "admin_password": "🔑 Parol kiriting:",
    "wrong_credentials": "❌ Login yoki parol xato!",

    # ── Admin – Menu ────────────────────────────────────────────────────
    "admin_menu_title": "⚙️ Admin Panel",
    "admin_categories": "📂 Kategoriyalar",
    "admin_products": "📦 Tovarlar",
    "admin_orders": "🛒 Buyurtmalar",
    "admin_statistics": "📊 Statistika",
    "admin_settings": "⚙️ Sozlamalar",
    "logout": "🚪 Chiqish",

    # ── Admin – Categories ──────────────────────────────────────────────
    "add_category": "➕ Kategoriya qo'shish",
    "category_list": "📋 Kategoriyalar",
    "edit_category": "✏️ Tahrirlash",
    "delete_category": "🗑 O'chirish",

    # ── Admin – Products ────────────────────────────────────────────────
    "add_product": "➕ Tovar qo'shish",
    "product_list": "📋 Tovarlar",
    "edit_product": "✏️ Tahrirlash",
    "change_price": "💰 Narx o'zgartirish",
    "change_stock": "📦 Ombor soni",
    "delete_product": "🗑 O'chirish",

    # ── Admin – Orders ──────────────────────────────────────────────────
    "search": "🔍 Qidirish",
    "new_orders": "🆕 Yangi",
    "delivering": "🚚 Yetkazilmoqda",
    "completed": "✅ Tugallangan",
    "cancelled": "❌ Bekor qilingan",

    # ── Admin – Statistics ──────────────────────────────────────────────
    "stats_title": (
        "📊 Statistika\n\n"
        "📦 Bugungi buyurtmalar: {today_orders}\n"
        "💰 Bugungi savdo: {today_sales} so'm\n"
        "💰 Oylik savdo: {monthly_sales} so'm\n"
        "👤 Foydalanuvchilar: {users}\n"
        "🏆 Eng ko'p sotilgan: {top_product}"
    ),

    # ── Admin – Settings ────────────────────────────────────────────────
    "payment_settings": "💳 To'lov sozlamalari",
    "delivery_price_btn": "🚚 Dostavka narxi",
    "delivery_area": "📍 Dostavka hududi",
    "manage_admins": "👨‍💼 Adminlar",
    "broadcast": "📢 Reklama yuborish",

    # ── Admin – Category CRUD ───────────────────────────────────────────
    "enter_category_name": "📝 Kategoriya nomini kiriting:",
    "send_category_image": "🖼 Kategoriya rasmini yuboring (yoki /skip):",
    "category_added": "✅ Kategoriya qo'shildi!",
    "category_deleted": "✅ Kategoriya o'chirildi!",
    "category_edited": "✅ Kategoriya tahrirlandi!",

    # ── Admin – Product CRUD ────────────────────────────────────────────
    "enter_product_name": "📝 Tovar nomini kiriting:",
    "choose_category_for_product": "📂 Kategoriyani tanlang:",
    "enter_price": "💰 Narxni kiriting (so'm):",
    "send_product_image": "🖼 Tovar rasmini yuboring (yoki /skip):",
    "enter_stock": "📦 Ombordagi sonini kiriting:",
    "product_added": "✅ Tovar qo'shildi!",
    "product_deleted": "✅ Tovar o'chirildi!",
    "product_edited": "✅ Tovar tahrirlandi!",
    "price_changed": "✅ Narx o'zgartirildi!",
    "stock_changed": "✅ Ombor soni yangilandi!",

    # ── Search ──────────────────────────────────────────────────────────
    "enter_search_query": "🔍 Qidiruv so'zini kiriting:",
    "no_results": "😕 Hech narsa topilmadi.",

    # ── Broadcast ───────────────────────────────────────────────────────
    "broadcast_enter": "📝 Reklama xabarini yuboring:",
    "broadcast_sent": "✅ Xabar {count} ta foydalanuvchiga yuborildi!",

    # ── Delivery ────────────────────────────────────────────────────────
    "enter_delivery_price": "💰 Yangi dostavka narxini kiriting (so'm):",
    "delivery_price_updated": "✅ Dostavka narxi yangilandi: {price} so'm",

    # ── Confirmation dialogs ────────────────────────────────────────────
    "confirm_delete": "❓ Rostdan o'chirmoqchimisiz?",
    "yes_delete": "✅ Ha, o'chirish",
    "no_cancel": "❌ Bekor qilish",

    # ── Order status updates ────────────────────────────────────────────
    "order_accepted": "✅ Buyurtma #{order_id} qabul qilindi!",
    "order_shipped": "🚚 Buyurtma #{order_id} yuborildi!",
    "order_cancelled": "❌ Buyurtma #{order_id} bekor qilindi!",

    # ── Alerts ──────────────────────────────────────────────────────────
    "low_stock_alert": "⚠️ Kam qolgan tovar:\n{name} - {stock} ta qoldi!",

    # ── Pagination ──────────────────────────────────────────────────────
    "page_info": "📄 Sahifa {current}/{total}",

    # ── Misc ────────────────────────────────────────────────────────────
    "item_added_to_cart": "✅ {name} savatchaga qo'shildi!",
    "select_product": "📦 Mahsulotni tanlang:",
    "select_category": "📂 Kategoriyani tanlang:",
    "no_categories": "📂 Kategoriyalar mavjud emas.",
    "no_products": "📦 Mahsulotlar mavjud emas.",
    "no_orders": "📋 Buyurtmalar mavjud emas.",
    "order_details": (
        "📋 Buyurtma #{order_id}\n\n"
        "👤 {name}\n📞 {phone}\n📍 {address}\n"
        "💳 {payment}\n📦 Status: {status}\n\n"
        "🛒 Mahsulotlar:\n{items}\n\n"
        "💰 Jami: {total} so'm"
    ),

    # ── Editing ─────────────────────────────────────────────────────────
    "enter_new_name": "📝 Yangi nomni kiriting:",
    "enter_new_price": "💰 Yangi narxni kiriting:",
    "enter_new_stock": "📦 Yangi sonni kiriting:",

    # ── Logout ──────────────────────────────────────────────────────────
    "logout_success": "✅ Tizimdan chiqdingiz.",

    # ── Admin management ────────────────────────────────────────────────
    "add_admin": "➕ Admin qo'shish",
    "enter_admin_login": "👤 Admin loginini kiriting:",
    "enter_admin_password": "🔑 Admin parolini kiriting:",
    "admin_added": "✅ Admin qo'shildi!",
    "admin_deleted": "✅ Admin o'chirildi!",

    # ── Language ────────────────────────────────────────────────────────
    "language_changed": "✅ Til o'zgartirildi!",
}
