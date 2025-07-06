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
    message: Message
):
    await message.answer_sticker("CAACAgIAAxkBAAEOtCJoTuX6lxQjhhDsQrQFlFXLS3bJLQACdF0AAmSIQEtmW6X_FuNIUDYE")


@router.callback_query(F.data == "create_tasklist")
@router.message(Command("create"))
async def create_task_list(
    event: CallbackQuery | Message, dialog_manager: DialogManager
):
    if isinstance(event, CallbackQuery):
        await event.answer()
    logger.debug(f"opening dialog for user {event.from_user.id}")
    await dialog_manager.start(CreateListDialog.main, data={"name": "Task List"})

@router.message(Command("lang"))
async def change_language(
    message: Message, i18n: I18nContext
):
    b = InlineKeyboardBuilder()
    b.button(text="🇺🇸 English", callback_data="change_lang:en")
    b.button(text="🇷🇺 Русский", callback_data="change_lang:ru")

    await message.reply(i18n.change.lang.msg(), reply_markup=b.as_markup())


@router.callback_query(F.data.startswith("change_lang:"))
async def change_lang(
    call: CallbackQuery, i18n: I18nContext
):
    lang = call.data.split(":")[1]
    await i18n.set_locale(lang)
    await call.answer(i18n.success())