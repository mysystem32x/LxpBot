from aiogram.fsm.state import StatesGroup, State

class LoginForm(StatesGroup):
    data = State()
