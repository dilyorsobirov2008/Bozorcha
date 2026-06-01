from aiogram.fsm.state import State, StatesGroup

class AdminLogin(StatesGroup):
    username = State()
    password = State()

class AddCategory(StatesGroup):
    name = State()

class EditCategory(StatesGroup):
    category_id = State()
    field = State()
    value = State()

class AddProduct(StatesGroup):
    name = State()
    price = State()
    photo = State()
    category = State()

class EditProduct(StatesGroup):
    product_id = State()
    field = State()
    value = State()

class BroadcastState(StatesGroup):
    message = State()
    confirm = State()

class SettingsState(StatesGroup):
    select = State()
    value = State()

class ProductSearch(StatesGroup):
    query = State()
