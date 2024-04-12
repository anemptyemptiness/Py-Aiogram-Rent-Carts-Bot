import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from config.config import config
from menu_commands import set_default_commands
from handlers import (
    router_start_shift,
    router_carts,
    router_authorise,
    router_finish_shift,
    router_encashment,
)
from handlers.admin_handler import router_admin

bot = Bot(token=config.tg_bot.token)
storage = RedisStorage(redis=config.redis)
dp = Dispatcher(storage=storage)

logging.basicConfig(level=logging.INFO)


async def main():
    # тут диспетчеры будут
    dp.include_router(router_authorise)
    dp.include_router(router_carts)
    dp.include_router(router_start_shift)
    dp.include_router(router_finish_shift)
    dp.include_router(router_encashment)
    dp.include_router(router_admin)

    await set_default_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
