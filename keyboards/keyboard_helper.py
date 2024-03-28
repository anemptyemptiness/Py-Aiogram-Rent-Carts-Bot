import json

from aiogram.utils.keyboard import InlineKeyboardButton, InlineKeyboardMarkup
from config.config import config


class KeyboardHelper:
    def __init__(self):
        self.buttons: dict[str, str] = {}

        for i in range(1, config.count_carts + 1):
            self.buttons[f"cart_{i}"] = f"Тележка #{i}✅"

    @staticmethod
    def change_btn_to_free(buttons, num_of_button: int):
        buttons[f"cart_{num_of_button}"] = f"Тележка #{num_of_button}✅"

    @staticmethod
    def change_btn_to_rent(buttons, num_of_button: int):
        buttons[f"cart_{num_of_button}"] = f"Тележка #{num_of_button}❌"

    @staticmethod
    def get_kb(buttons):
        buttons_lst = list()
        kb = list()

        count_carts = config.count_carts

        for cb, name in buttons.items():
            buttons_lst.append(InlineKeyboardButton(
                text=name, callback_data=cb,
            ))

        if config.count_carts % 2 == 0:
            count_carts += 1

        for i in range(1, count_carts, 2):
            kb.append([buttons_lst[i - 1], buttons_lst[i]])

        # если нечетное кол-во, то верну последнюю кнопку, которую вычел вначале
        if config.count_carts % 2 != 0:
            kb.append([buttons_lst[count_carts]])

        return InlineKeyboardMarkup(inline_keyboard=kb)

    @staticmethod
    def reset_keyboard():
        kb = []
        count_carts = config.count_carts

        # если нечетное количество, то уменьшу на 1, чтобы сделать 2 ряда кнопок
        if config.count_carts % 2 == 0:
            count_carts += 1

        for i in range(2, count_carts, 2):
            kb.append(
                [
                    InlineKeyboardButton(
                        text=f"Тележка #{i - 1}✅",
                        callback_data=f"cart_{i - 1}",
                    ),
                    InlineKeyboardButton(
                        text=f"Тележка #{i}✅",
                        callback_data=f"cart_{i}"
                    ),
                ]
            )

        # если нечетное кол-во, то верну последнюю кнопку, которую вычел вначале
        if config.count_carts % 2 != 0:
            kb.append([
                InlineKeyboardButton(
                    text=f"Тележка #{count_carts}✅",
                    callback_data=f"cart_{count_carts}"),
            ])

        return InlineKeyboardMarkup(inline_keyboard=kb)
