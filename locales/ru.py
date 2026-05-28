"""Russian language texts for the supermarket bot."""

texts: dict[str, str] = {
    # ── General ─────────────────────────────────────────────────────────
    "welcome": "Здравствуйте! 👋\nДобро пожаловать в наш бот.",
    "choose_language": "🌐 Выберите язык:",
    "lang_uz": "🇺🇿 O'zbekcha",
    "lang_ru": "🇷🇺 Русский",
    "main_menu": "🏠 Главное меню",
    "shopping": "🛒 Покупки",
    "admin_panel": "🔐 Админ панель",

    # ── Categories ──────────────────────────────────────────────────────
    "categories_title": "📂 Выберите категорию:",
    "drinks": "🥤 Напитки",
    "sweets": "🍫 Сладости",
    "meat": "🥩 Мясо",
    "dairy": "🥛 Молочные продукты",
    "vegetables": "🥦 Овощи",
    "household": "🧼 Бытовая химия",
    "back": "⬅️ Назад",

    # ── Product ─────────────────────────────────────────────────────────
    "product_info": "📦 {name}\n💰 {price} сум\n📦 На складе: {stock} шт",
    "in_stock": "📦 На складе: {stock} шт",
    "add_to_cart": "🛒 Добавить в корзину",

    # ── Cart ────────────────────────────────────────────────────────────
    "cart_title": "🛒 Ваша корзина:",
    "cart_empty": "🛒 Корзина пуста",
    "cart_item": "• {name} x{quantity} = {total} сум",
    "cart_total": "\n💰 Итого: {total} сум",
    "clear_cart": "🗑 Очистить",

    # ── Order ───────────────────────────────────────────────────────────
    "order_btn": "🚚 Оформить заказ",
    "send_address": "📍 Отправьте ваш адрес (текст или локация):",
    "send_phone": "📞 Отправьте ваш номер телефона:",
    "share_phone": "📱 Поделиться номером",
    "choose_payment": "💳 Выберите способ оплаты:",
    "cash": "💵 Наличные",
    "click_pay": "💳 Click",
    "payme_pay": "💳 Payme",
    "order_confirmed": (
        "✅ Ваш заказ принят!\n\n"
        "📋 Номер заказа: #{order_id}\n"
        "💰 Итого: {total} сум\n\n"
        "Мы скоро свяжемся с вами!"
    ),
    "order_notification": (
        "🆕 Новый заказ #{order_id}\n\n"
        "👤 {name}\n📞 {phone}\n📍 {address}\n\n"
        "🛒 Товары:\n{items}\n\n"
        "💰 Итого: {total} сум\n💳 Оплата: {payment}"
    ),
    "accept_order": "✅ Принять",
    "shipped_order": "🚚 Отправлен",
    "cancel_order": "❌ Отменить",

    # ── Admin – Auth ────────────────────────────────────────────────────
    "admin_login": "👤 Введите логин:",
    "admin_password": "🔑 Введите пароль:",
    "wrong_credentials": "❌ Неверный логин или пароль!",

    # ── Admin – Menu ────────────────────────────────────────────────────
    "admin_menu_title": "⚙️ Админ панель",
    "admin_categories": "📂 Категории",
    "admin_products": "📦 Товары",
    "admin_orders": "🛒 Заказы",
    "admin_statistics": "📊 Статистика",
    "admin_settings": "⚙️ Настройки",
    "logout": "🚪 Выход",

    # ── Admin – Categories ──────────────────────────────────────────────
    "add_category": "➕ Добавить категорию",
    "category_list": "📋 Категории",
    "edit_category": "✏️ Редактировать",
    "delete_category": "🗑 Удалить",

    # ── Admin – Products ────────────────────────────────────────────────
    "add_product": "➕ Добавить товар",
    "product_list": "📋 Товары",
    "edit_product": "✏️ Редактировать",
    "change_price": "💰 Изменить цену",
    "change_stock": "📦 Количество на складе",
    "delete_product": "🗑 Удалить",

    # ── Admin – Orders ──────────────────────────────────────────────────
    "search": "🔍 Поиск",
    "new_orders": "🆕 Новые",
    "delivering": "🚚 Доставляются",
    "completed": "✅ Завершённые",
    "cancelled": "❌ Отменённые",

    # ── Admin – Statistics ──────────────────────────────────────────────
    "stats_title": (
        "📊 Статистика\n\n"
        "📦 Заказы сегодня: {today_orders}\n"
        "💰 Продажи сегодня: {today_sales} сум\n"
        "💰 Продажи за месяц: {monthly_sales} сум\n"
        "👤 Пользователи: {users}\n"
        "🏆 Самый продаваемый: {top_product}"
    ),

    # ── Admin – Settings ────────────────────────────────────────────────
    "payment_settings": "💳 Настройки оплаты",
    "delivery_price_btn": "🚚 Стоимость доставки",
    "delivery_area": "📍 Зона доставки",
    "manage_admins": "👨‍💼 Администраторы",
    "broadcast": "📢 Рассылка",

    # ── Admin – Category CRUD ───────────────────────────────────────────
    "enter_category_name": "📝 Введите название категории:",
    "send_category_image": "🖼 Отправьте изображение категории (или /skip):",
    "category_added": "✅ Категория добавлена!",
    "category_deleted": "✅ Категория удалена!",
    "category_edited": "✅ Категория обновлена!",

    # ── Admin – Product CRUD ────────────────────────────────────────────
    "enter_product_name": "📝 Введите название товара:",
    "choose_category_for_product": "📂 Выберите категорию:",
    "enter_price": "💰 Введите цену (сум):",
    "send_product_image": "🖼 Отправьте фото товара (или /skip):",
    "enter_stock": "📦 Введите количество на складе:",
    "product_added": "✅ Товар добавлен!",
    "product_deleted": "✅ Товар удалён!",
    "product_edited": "✅ Товар обновлён!",
    "price_changed": "✅ Цена изменена!",
    "stock_changed": "✅ Количество обновлено!",

    # ── Search ──────────────────────────────────────────────────────────
    "enter_search_query": "🔍 Введите слово для поиска:",
    "no_results": "😕 Ничего не найдено.",

    # ── Broadcast ───────────────────────────────────────────────────────
    "broadcast_enter": "📝 Отправьте сообщение для рассылки:",
    "broadcast_sent": "✅ Сообщение отправлено {count} пользователям!",

    # ── Delivery ────────────────────────────────────────────────────────
    "enter_delivery_price": "💰 Введите новую стоимость доставки (сум):",
    "delivery_price_updated": "✅ Стоимость доставки обновлена: {price} сум",

    # ── Confirmation dialogs ────────────────────────────────────────────
    "confirm_delete": "❓ Вы уверены, что хотите удалить?",
    "yes_delete": "✅ Да, удалить",
    "no_cancel": "❌ Отмена",

    # ── Order status updates ────────────────────────────────────────────
    "order_accepted": "✅ Заказ #{order_id} принят!",
    "order_shipped": "🚚 Заказ #{order_id} отправлен!",
    "order_cancelled": "❌ Заказ #{order_id} отменён!",

    # ── Alerts ──────────────────────────────────────────────────────────
    "low_stock_alert": "⚠️ Мало товара:\n{name} - осталось {stock} шт!",

    # ── Pagination ──────────────────────────────────────────────────────
    "page_info": "📄 Страница {current}/{total}",

    # ── Misc ────────────────────────────────────────────────────────────
    "item_added_to_cart": "✅ {name} добавлен в корзину!",
    "select_product": "📦 Выберите товар:",
    "select_category": "📂 Выберите категорию:",
    "no_categories": "📂 Нет категорий.",
    "no_products": "📦 Нет товаров.",
    "no_orders": "📋 Нет заказов.",
    "order_details": (
        "📋 Заказ #{order_id}\n\n"
        "👤 {name}\n📞 {phone}\n📍 {address}\n"
        "💳 {payment}\n📦 Статус: {status}\n\n"
        "🛒 Товары:\n{items}\n\n"
        "💰 Итого: {total} сум"
    ),

    # ── Editing ─────────────────────────────────────────────────────────
    "enter_new_name": "📝 Введите новое название:",
    "enter_new_price": "💰 Введите новую цену:",
    "enter_new_stock": "📦 Введите новое количество:",

    # ── Logout ──────────────────────────────────────────────────────────
    "logout_success": "✅ Вы вышли из системы.",

    # ── Admin management ────────────────────────────────────────────────
    "add_admin": "➕ Добавить админа",
    "enter_admin_login": "👤 Введите логин админа:",
    "enter_admin_password": "🔑 Введите пароль админа:",
    "admin_added": "✅ Админ добавлен!",
    "admin_deleted": "✅ Админ удалён!",

    # ── Language ────────────────────────────────────────────────────────
    "language_changed": "✅ Язык изменён!",
}
