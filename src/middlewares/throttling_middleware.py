from typing import Callable, Any, Awaitable, Dict

from aiogram import BaseMiddleware, Bot
from aiogram.types import CallbackQuery, TelegramObject, User
from cachetools import TTLCache

CACHE = TTLCache(maxsize=5000, ttl=2)


class ThrottlingMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: CallbackQuery,
            data: Dict[str, Any],
    ):
        user: User = data.get("event_from_user")
        if user.id in CACHE:
            await event.answer("⏳Подождите")
            return

        CACHE[user.id] = True

        return await handler(event, data)
