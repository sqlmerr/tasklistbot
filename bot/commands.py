from aiogram import Bot
from aiogram.types import BotCommandScopeDefault, BotCommand


async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Restart bot"),
        BotCommand(command="create", description="Create new task list"),
        BotCommand(command="my", description="Get your task lists"),
    ]

    return await bot.set_my_commands(
        commands,
        BotCommandScopeDefault(),
    )
