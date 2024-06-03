from aiogram.utils.keyboard import InlineKeyboardButton, InlineKeyboardMarkup
from src.callbacks.cart_callback import CartCallbackFactory
from src.db import DB_mongo, DB
from src.db.postgre.dao import AsyncOrm


async def get_keyboard(place):
    ids = DB_mongo.get_ids_carts_from_place(place=place)
    statuses = DB_mongo.get_statuses_carts_from_place(place=place)

    count_carts = await AsyncOrm.get_count_carts_from_place(title=place)
    temp_count = await AsyncOrm.get_count_carts_from_place(title=place)

    kb = []

    # если нечетное количество, то уменьшу на 1, чтобы сделать 2 ряда кнопок
    if temp_count % 2 == 0:
        count_carts += 1

    for i in range(1, count_carts, 2):
        kb.append([
            InlineKeyboardButton(
                text=f"Тележка #{ids[i - 1]}{'✅' if statuses[i - 1] == 'free' else '❌'}",
                callback_data=CartCallbackFactory(
                    title_place=place,
                    number=ids[i - 1],
                    status=statuses[i - 1],
                ).pack(),
            ),
            InlineKeyboardButton(
                text=f"Тележка #{ids[i]}{'✅' if statuses[i] == 'free' else '❌'}",
                callback_data=CartCallbackFactory(
                    title_place=place,
                    number=ids[i],
                    status=statuses[i],
                ).pack(),
            ),
        ])

    # если четное кол-во, то верну последнюю кнопку, которую вычел в начале
    if temp_count % 2 != 0:
        kb.append([
            InlineKeyboardButton(
                text=f"Тележка #{count_carts}{'✅' if statuses[count_carts - 1] == 'free' else '❌'}",
                callback_data=CartCallbackFactory(
                    title_place=place,
                    number=f"{count_carts}",
                    status=statuses[count_carts - 1],
                ).pack()
            ),
        ])

    kb.append([InlineKeyboardButton(text="Оформить отчёт", callback_data="report_carts")])
    kb.append([InlineKeyboardButton(text="Вернуться в меню", callback_data="go_back_to_menu")])

    return InlineKeyboardMarkup(inline_keyboard=kb)
