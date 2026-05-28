from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    """FSM states for user-facing flows."""

    choosing_language = State()
    in_main_menu = State()
    browsing_categories = State()
    browsing_products = State()
    viewing_product = State()
    in_cart = State()
    entering_address = State()
    entering_phone = State()
    choosing_payment = State()
