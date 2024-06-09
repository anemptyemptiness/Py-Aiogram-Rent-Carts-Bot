from datetime import datetime, timezone, timedelta

import pymongo.errors
from pymongo import MongoClient

from src.config import Settings
from src.db.postgre.dao import AsyncOrm
from src.lexicon.lexicon_ru import TO_FREE
from src.db.postgre.postgre_db import DataBase


class MongoDB:
    def __init__(self, settings: Settings):
        '''
        _today - коллекция для сегодняшнего дня, хранящая точки,
                 которые хранят информацию о сообщении с клавиатурой на данной точке
        _carts_today - коллекция точек, храняющая тележки, которые хранят информацию о себе
        '''

        self._client = MongoClient(f"mongodb://{settings.MONGODB_HOST}:{settings.MONGODB_PORT}")
        self._today = self._client[settings.MONGODB_NAME][settings.MONGODB_TODAY]
        self._carts_today = self._client[settings.MONGODB_NAME][settings.MONGODB_CARTS_TODAY]
        self._postgreDB = DataBase(settings=settings)

    def check_for_carts_today_collection_by_place(self, place):
        return True if self._carts_today.find_one({place: {"$exists": True}}) else False

    async def reset_carts_from_place(self, place):
        carts_data = {}
        for i in range(1, await AsyncOrm.get_count_carts_from_place(title=place) + 1):
            cart_data = {
                f"cart_{i}": {"_id": str(i), "end_time": 0, "start_time": 0, "status": "free", "total_time": []}
            }
            carts_data.update(cart_data)

        self._carts_today.update_one(
            {place: {"$exists": True}},
            {"$set": {place: carts_data}},
            upsert=True,
        )
        
    def drop_today_for_current_person_on_place(self, chat_id, place):
        try:
            self._today.delete_one(
                {f"{place}._id": str(chat_id)},
            )
        except pymongo.errors.PyMongoError:
            pass

    def reset_today_from_place(self, chat_id, place):
        self._today.update_one(
            {f"{place}._id": str(chat_id)},
            {"$set": {place: {"_id": str(chat_id), "message_id": 0, "chat_id": 0}}},
            upsert=True,
        )

    def update_today(self, place, message_id, chat_id):
        today_data = {"_id": str(chat_id), "message_id": str(message_id), "chat_id": str(chat_id)}

        self._today.update_one(
            {f"{place}._id": str(chat_id)},
            {"$set": {place: today_data}},
            upsert=True,
        )

    def update_info_cart_from_place(self, place, number_of_cart, to_status, time=None):
        carts_today_place_data = self._carts_today.find_one({place: {"$exists": True}})[place]

        # если тележка была в аренде и теперь ее освобождают
        if to_status == TO_FREE:
            time_now = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime("%H:%M")
            start_time_str = carts_today_place_data[f"cart_{number_of_cart}"].get("start_time")

            # переделываю строку "%H:%M" в экземпляр класса datetime
            start_time = datetime.strptime(str(start_time_str), "%H:%M")
            time_now = datetime.strptime(time_now, "%H:%M")

            total_time = time_now - start_time  # HH:MM:SS - формат этой переменной
            hours, minutes, _ = str(total_time).split(":")

            self._carts_today.update_one(
                {f"{place}.cart_{number_of_cart}": {"$exists": True}},
                {"$set": {
                    f"{place}.cart_{number_of_cart}.status": to_status,
                    f"{place}.cart_{number_of_cart}.start_time": 0,
                }},
            )
            self._carts_today.update_one(
                {f"{place}.cart_{number_of_cart}": {"$exists": True}},
                {"$push": {
                    f"{place}.cart_{number_of_cart}.total_time": f"{hours}ч. {minutes}мин."
                }},
            )

        # если тележка была свободна и теперь ее арендуют
        else:
            self._carts_today.update_one(
                {f"{place}.cart_{number_of_cart}": {"$exists": True}},
                {"$set": {
                    f"{place}.cart_{number_of_cart}.start_time": str(time),
                    f"{place}.cart_{number_of_cart}.status": to_status,
                }}
            )

        # возвращаю статус тележки
        return self._carts_today.find_one(
            {},
            {f"{place}.cart_{number_of_cart}.status": 1}
        )[place][f"cart_{number_of_cart}"]["status"]

    def get_ids_carts_from_place(self, place):
        carts_data = self._carts_today.find_one({place: {"$exists": True}})[place]
        return [carts_data[cart].get("_id") for cart in carts_data]

    def get_statuses_carts_from_place(self, place):
        carts_data = self._carts_today.find_one({place: {"$exists": True}})[place]
        return [carts_data[cart].get("status") for cart in carts_data]

    def get_inline_markup_message_chat_ids_from_place(self, place):
        chats_data = self._today.find({place: {"$exists": True}})
        return [(int(data[place]['chat_id']), int(data[place]['message_id'])) for data in chats_data]

    def get_total_time_carts_from_place(self, place):
        carts_data = self._carts_today.find_one({place: {"$exists": True}})[place]
        return [(cart, carts_data[cart].get("total_time")) for cart in carts_data]

    def drop_today_from_place(self, place):
        self._today.delete_many({place: {"$exists": True}})

    def drop_carts_today_from_place(self, place):
        self._carts_today.delete_many({place: {"$exists": True}})
