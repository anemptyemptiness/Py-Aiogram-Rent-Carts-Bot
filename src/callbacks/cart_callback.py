from aiogram.filters.callback_data import CallbackData


class CartCallbackFactory(CallbackData, prefix="cart"):
    title_place: str
    number: str
    status: str
