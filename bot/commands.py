from aiogram import Bot
from aiogram.types import BotCommandScopeDefault, BotCommand


async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="create", description="Create new task list"),
        BotCommand(command="my", description="Get your task lists"),
        BotCommand(command="lang", description="Change language"),
        BotCommand(command="start", description="Start"),
    ]

    return await bot.set_my_commands(
        commands,
        BotCommandScopeDefault(),
    )
