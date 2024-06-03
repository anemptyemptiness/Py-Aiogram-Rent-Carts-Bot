from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from src.callbacks.place import PlaceCallbackFactory
from src.db.postgre.dao import AsyncOrm


async def create_places_kb() -> InlineKeyboardMarkup:
    kb = []

    for chat_id, title, count_carts in await AsyncOrm.get_places_chat_id_title_count_carts():
        kb.append([
            InlineKeyboardButton(text=title, callback_data=PlaceCallbackFactory(
                title=title,
                chat_id=int(chat_id),
                count_carts=int(count_carts),
                ).pack(),
            )
        ])

    kb.append([InlineKeyboardButton(text="Отмена", callback_data="cancel")])

    return InlineKeyboardMarkup(
        inline_keyboard=kb,
    )


def create_yes_no_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да", callback_data="yes"),
             InlineKeyboardButton(text="Нет", callback_data="no")],
            [InlineKeyboardButton(text="Отмена", callback_data="cancel")],
        ],
    )


def create_rules_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Согласен", callback_data="agree")],
        ],
    )


def create_cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отмена")],
        ],
        resize_keyboard=True,
    )


def create_agree_kb() -> InlineKeyboardMarkup:
    return  InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Ознакомился", callback_data="agree")],
            [InlineKeyboardButton(text="Отмена", callback_data="cancel")],
        ]
    )