from aiogram import types, Bot


async def set_default_commands(bot: Bot):
    await bot.set_my_commands([
        types.BotCommand(command="start_shift", description="Открытие смены"),
        types.BotCommand(command="carts", description="Открыть список тележек"),
        types.BotCommand(command="finish_shift", description="Закрытие смены"),
        types.BotCommand(command="encashment", description="Инкассация"),
        types.BotCommand(command="admin", description="Админка"),
    ])
