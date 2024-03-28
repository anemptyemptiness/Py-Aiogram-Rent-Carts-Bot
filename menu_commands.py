from aiogram import types, Bot


async def set_default_commands(bot: Bot):
    await bot.set_my_commands([
        types.BotCommand(command="carts_cars", description="Открыть список тележек/машинок"),
    ])
