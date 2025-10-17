from aiogram.fsm.state import StatesGroup, State

class State(StatesGroup):
    ban = State()
    unban = State()
    add = State()
    change = State()
    add_news = State()