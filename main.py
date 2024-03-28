import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from config.config import config
from menu_commands import set_default_commands
from handlers import authorise, default_carts_cars

bot = Bot(token=config.tg_bot.token)
storage = RedisStorage(redis=config.redis)
dp = Dispatcher(storage=storage)

logging.basicConfig(level=logging.INFO)


async def main():
    # тут диспетчеры будут
    dp.include_router(authorise.router_authorise)
    dp.include_router(default_carts_cars.router_carts)

    await set_default_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
