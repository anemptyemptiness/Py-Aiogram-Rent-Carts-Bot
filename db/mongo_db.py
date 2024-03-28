from datetime import datetime, timezone, timedelta

from pymongo import MongoClient
from aiogram.types import Message
from aiogram import Bot

from config.config import Config, config


class MongoDB:
    def __init__(self, config: Config):
        '''
        _today - коллекция для сегодняшнего дня, хранящая информацию о сообщении
        _carts_today - коллекция тележек, хранящая информацию о тележках
        '''

        self._client = MongoClient(f"mongodb://{config.host_mdb}:{config.port_mdb}")
        self._today = self._client[config.db_name_mdb][config.today_mdb]
        self._carts_today = self._client[config.db_name_mdb][config.carts_today_mdb]

    def update_today(self, message_id, chat_id):
        self._today.update_one(
            {"_id": f"{chat_id}"},
            {"$set": {f"{chat_id}": f"{message_id}", "chat_id": f"{chat_id}"}},
            upsert=True,
        )

    def reset_carts(self):
        for i in range(1, config.count_carts + 1):
            self._carts_today.update_one(
                {"_id": f"{i}"},
                {"$set": {"status": "free", "start_time": 0, "total_time": []}},
                upsert=True,
            )

    def update_info_cart(self, number_of_cart, to_status, time=None):
        # если тележка была в аренде и теперь ее освобождают
        if to_status == "free":
            time_now = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime("%H:%M")
            start_time_str = self._carts_today.find_one({"_id": f"{number_of_cart}"})["start_time"]

            # переделываю строку "%H:%M" в экземпляр класса datetime
            start_time = datetime.strptime(start_time_str, "%H:%M")
            time_now = datetime.strptime(time_now, "%H:%M")

            total_time = time_now - start_time  # HH:MM:SS - формат этой переменной
            hours, minutes, _ = str(total_time).split(":")

            self._carts_today.update_one(
                {"_id": f"{number_of_cart}"},
                {"$set": {"status": f"{to_status}", "start_time": 0}},
            )
            self._carts_today.update_one(
                {"_id": f"{number_of_cart}"},
                {"$push": {"total_time": f"{hours}ч. {minutes}мин."}},
            )

        # если тележка была свободна и теперь ее арендуют
        else:
            self._carts_today.update_one(
                {"_id": f"{number_of_cart}"},
                {"$set": {"status": f"{to_status}", "start_time": f"{time}"}},
            )

        # возвращаю статус тележки
        return self._carts_today.find_one({"_id": f"{number_of_cart}"})["status"]

    def get_last_message_id_info(self, user_id):
        return self._today.find_one({"_id": f"{user_id}"})[f"{user_id}"]

    def update_messages(self):
        pass
