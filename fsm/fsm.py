from aiogram.fsm.state import StatesGroup, State


class Authorise(StatesGroup):
    fullname = State()


class FSMWorkingDay(StatesGroup):
    first_time = State()  # первый запуск, чтобы залить новую клавиатуру
    working_day = State()  # запуск клавиатур в рамках рабочего дня
