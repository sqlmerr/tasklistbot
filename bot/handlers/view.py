import secrets

from aiogram import Bot, Router, F
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    CallbackQuery,
    Message,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from aiogram_dialog import DialogManager
from aiogram_i18n import I18nContext
from beanie import PydanticObjectId

from bot.db.models import SecurityRuleType, TaskList, User
from bot.db.requests import get_task_lists_by_user
from bot.dialogs.states import ListViewerDialog
from bot.utils.calldata import OptionClickData
from bot.utils.permissions import ensure_user_has_permission

router = Router()


@router.inline_query(F.query.startswith("open:"))
async def open_tasklist(query: InlineQuery, i18n: I18nContext):
    list_id = query.query.split(":")[-1]
    if not PydanticObjectId.is_valid(list_id):
        await query.answer(
            [
                InlineQueryResultArticle(
                    id=secrets.token_urlsafe(16),
                    title=i18n.invalid.id(),
                    input_message_content=InputTextMessageContent(
                        message_text=f"Not a valid id: {list_id}"
                    ),
                )
            ]
        )
        return

    tasklist = await TaskList.get(list_id, fetch_links=True)
    if not tasklist or not ensure_user_has_permission(
        tasklist, query.from_user.id, permission="read"
    ):
        await query.answer(
            [
                InlineQueryResultArticle(
                    id=secrets.token_urlsafe(16),
                    title=i18n.get("not-found"),
                    input_message_content=InputTextMessageContent(
                        message_text=f"Task list with id {list_id} not found or you have not allowed to read it."
                    ),
                )
            ]
        )
        return
    markup = generate_tasklist_markup(tasklist)
    await query.answer(
        [
            InlineQueryResultArticle(
                id=secrets.token_urlsafe(16),
                title=tasklist.title,
                input_message_content=InputTextMessageContent(
                    message_text=tasklist.title,
                ),
                reply_markup=markup,
            )
        ],
        cache_time=5
    )


def generate_tasklist_markup(tasklist: TaskList) -> InlineKeyboardMarkup:
    print(tasklist.options)
    b = InlineKeyboardBuilder()
    for i, o in enumerate(tasklist.options):
        b.button(
            text=f"{i}. {o.name} " + ("✅" if o.completed else ""),
            callback_data=OptionClickData(
                list_id=str(tasklist.id), option_index=i
            ),
        )

    b.adjust(1)
    return b.as_markup()


@router.callback_query(OptionClickData.filter())
async def option_click(
    call: CallbackQuery, callback_data: OptionClickData, i18n: I18nContext, bot: Bot
):
    tasklist = await TaskList.get(callback_data.list_id, fetch_links=True)
    if not tasklist:
        return

    if not ensure_user_has_permission(
        tasklist, call.from_user.id, "mark_tasks_as_completed"
    ):
        await call.answer(i18n.get("not-allowed"))
        return
    await call.answer()

    tasklist.options[callback_data.option_index].completed = not tasklist.options[
        callback_data.option_index
    ].completed
    await tasklist.save()

    markup = generate_tasklist_markup(tasklist)
    if not call.message:
        await bot.edit_message_reply_markup(
            inline_message_id=call.inline_message_id, reply_markup=markup
        )
    else:
        await bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
        )


@router.message(Command("my"))
async def get_all_lists(message: Message, user: User, i18n: I18nContext):
    tasklists = await get_task_lists_by_user(user.id)
    b = InlineKeyboardBuilder()
    for t in tasklists:
        b.button(text=t.title, callback_data=f"open:{t.id}")
    b.adjust(1)

    await message.reply(i18n.tasklist.all.msg(), reply_markup=b.as_markup())

@router.callback_query(F.data.startswith("open:"))
async def open_list(call: CallbackQuery, dialog_manager: DialogManager):
    tasklist_id = call.data.split(":")[1]
    tasklist = await TaskList.get(tasklist_id)
    if not tasklist:
        return
    await call.answer()
    await dialog_manager.start(ListViewerDialog.main, data={"tasklist_id": str(tasklist.id)})
