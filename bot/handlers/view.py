import secrets

from aiogram import Router, F
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_i18n import I18nContext
from beanie import PydanticObjectId

from bot.db.models import TaskList
from bot.utils.calldata import OptionClickData

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
                    )
                )
            ]
        )
        return
    
    tasklist = await TaskList.get(list_id, fetch_links=True)
    if not tasklist or tasklist.user.user_id != query.from_user.id:
        await query.answer(
            [
                InlineQueryResultArticle(
                    id=secrets.token_urlsafe(16),
                    title=i18n.get("not-found"),
                    input_message_content=InputTextMessageContent(
                        message_text=f"Task list with id {list_id} not found"
                    )
                )
            ]
        )
        return
    await query.answer(
        [
            InlineQueryResultArticle(
                id=secrets.token_urlsafe(16),
                title=tasklist.title,
                input_message_content=InputTextMessageContent(
                    message_text=tasklist.title,
                ),
                reply_markup=generate_tasklist_markup(tasklist)
            )
        ]
    )


def generate_tasklist_markup(tasklist: TaskList) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for i, o in enumerate(tasklist.options):
        b.button(text=f"{i}. {o.name} " + ("✅" if o.completed else ""), callback_data=OptionClickData(list_id=str(tasklist.id), option_index=i, user_id=tasklist.user.user_id))

    b.adjust(1)
    return b.as_markup()

@router.callback_query(OptionClickData.filter())
async def option_click(call: CallbackQuery, callback_data: OptionClickData, i18n: I18nContext):
    if callback_data.user_id != call.from_user.id:
        await call.answer(i18n.get("not-allowed"))
        return
    await call.answer()

    tasklist = await TaskList.get(callback_data.list_id, fetch_links=True)
    if not tasklist:
        await call.bot.edit_message_reply_markup(inline_message_id=call.inline_message_id, reply_markup=InlineKeyboardMarkup(inline_keyboard=[]))
        return
    
    tasklist.options[callback_data.option_index].completed = not tasklist.options[callback_data.option_index].completed
    await tasklist.save()

    markup = generate_tasklist_markup(tasklist)
    await call.bot.edit_message_reply_markup(inline_message_id=call.inline_message_id, reply_markup=markup)
    