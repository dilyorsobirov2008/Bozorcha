from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    """FSM states for admin panel flows."""

    entering_login = State()
    entering_password = State()
    in_admin_menu = State()
    in_categories_menu = State()
    adding_category_name = State()
    adding_category_image = State()
    selecting_category_edit = State()
    editing_category_name = State()
    selecting_category_delete = State()
    in_products_menu = State()
    adding_product_name = State()
    adding_product_category = State()
    adding_product_price = State()
    adding_product_image = State()
    adding_product_stock = State()
    selecting_product = State()
    editing_product_name = State()
    editing_product_price = State()
    editing_product_stock = State()
    in_orders_menu = State()
    viewing_orders = State()
    searching_products = State()
    entering_broadcast = State()
    entering_delivery_price = State()
    adding_admin_login = State()
    adding_admin_password = State()
