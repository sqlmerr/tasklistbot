import logging

from contextlib import suppress
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, InlineQuery, CallbackQuery
from aiogram_i18n import I18nContext
from bot.db import get_user
from bot.db.models import User

logger = logging.getLogger(__name__)


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message | InlineQuery | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | InlineQuery | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        i18n: I18nContext = data["i18n"]
        user = await get_user(event.from_user.id)
        if not user:
            user = User(user_id=event.from_user.id)

            await user.insert()
            logger.debug(f"registered new user with id {event.from_user.id}")
            with suppress(Exception):
                msg_to_pin = await event.bot.send_message(
                    user.user_id,
                    i18n.newbie.msg(
                        user=event.from_user.first_name,
                        bot_username=(await event.bot.me()).username,
                    )
                )
                await msg_to_pin.pin()
        data["user"] = user

        return await handler(event, data)
