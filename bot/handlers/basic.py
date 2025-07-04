import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_dialog import DialogManager

from aiogram_i18n import I18nContext

from bot.db import User
from bot.dialogs.create_list import CreateListDialog

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("start"))
async def start_cmd(
    message: Message, user: User, i18n: I18nContext, dialog_manager: DialogManager
):
    await message.reply(i18n.start.msg(user=message.from_user.first_name))


@router.callback_query(F.data == "create_tasklist")
@router.message(Command("create"))
async def create_task_list(
    event: CallbackQuery | Message, dialog_manager: DialogManager
):
    if isinstance(event, CallbackQuery):
        await event.answer()
    logger.debug(f"opening dialog for user {event.from_user.id}")
    await dialog_manager.start(CreateListDialog.main, data={"name": "Task List"})
