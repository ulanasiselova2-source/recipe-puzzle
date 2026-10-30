from aiogram.fsm.state import State, StatesGroup


class GameStates(StatesGroup):
    """Конечный автомат игры: выбор кухни -> вопрос -> результат."""

    choosing_country = State()
    choosing_ingredients = State()
    showing_result = State()


class SettingsStates(StatesGroup):
    confirming_reset = State()
