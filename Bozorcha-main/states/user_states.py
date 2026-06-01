from aiogram.fsm.state import State, StatesGroup

class OrderState(StatesGroup):
    address = State()
    phone = State()
    payment = State()
    confirm = State()
