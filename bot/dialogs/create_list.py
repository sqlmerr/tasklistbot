from typing import Any, TypedDict
from aiogram import F
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, SwitchTo, ListGroup, Back, Row
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import TextInput

from bot.db.models import TaskList, TaskOption, User
from bot.utils.widgets.i18n_format import I18NFormat
from bot.utils.widgets.copy_button import CopyButton


class Option(TypedDict):
    id: int
    content: str


class CreateListDialog(StatesGroup):
    main = State()
    add_option = State()
    settings = State()
    change_name = State()
    done = State()


async def show_alert(c: CallbackQuery, _: Button, manager: DialogManager):
    await c.answer("❗️ Test", show_alert=True, cache_time=0)
    await c.message.delete()
    await manager.done()


async def getter(dialog_manager: DialogManager, **kwargs) -> dict:
    name = dialog_manager.dialog_data.get("name", "Task list")
    options: list[str] = dialog_manager.dialog_data.get("options", [])
    return {
        "name": name,
        "options": [{"id": i, "content": o} for i, o in enumerate(options)],
        "can_be_completed": len(options) > 0
    }

async def share_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    share = dialog_manager.dialog_data.get("share")
    return {
        "share": share
    }


async def create_option(
    message: Message,
    widget: Any,
    dialog_manager: DialogManager,
    data: str
):
    options: list[str] = dialog_manager.dialog_data.get("options", [])
    options.append(data)
    dialog_manager.dialog_data["options"] = options
    await dialog_manager.switch_to(CreateListDialog.main)


async def rename_tasklist(
    message: Message,
    widget: Any,
    dialog_manager: DialogManager,
    data: str
):
    dialog_manager.dialog_data["name"] = data
    await dialog_manager.switch_to(CreateListDialog.settings)

async def done(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await callback.answer()
    name = str(manager.dialog_data.get("name", "Task list"))
    options = manager.dialog_data.get("options", [])
    user: User = manager.middleware_data["user"]
    tasklist = TaskList(
        title=name,
        user=user,
        options=[TaskOption(name=o, completed=False) for o in options]
    )
    await tasklist.insert()
    bot_username = (await callback.bot.me()).username
    share = f"@{bot_username} open {tasklist.id}"
    manager.dialog_data["share"] = share
    await manager.switch_to(CreateListDialog.done)


ui = Dialog(
    Window(
        I18NFormat("tasklist-menu-msg", name=Format("{name}")),
        ListGroup(
            Button(
                Format("{item[id]}. {item[content]}"),
                id="option_button"
            ),
            id="options_list", items="options", item_id_getter=lambda item: item["id"]
        ),
        SwitchTo(Const("+"), id="add_option", state=CreateListDialog.add_option),
        Row(
            SwitchTo(I18NFormat("tasklist-settings-btn"), id="switch_to_settings", state=CreateListDialog.settings),
            Button(Const("done"), id="done", on_click=done, when="can_be_completed"),
        ),

        state=CreateListDialog.main
    ),
    Window(
        I18NFormat("tasklist-option-create-msg"),
        TextInput(id="option_input", filter=F.text.len() <= 32, on_success=create_option),
        Back(Const("<-")),
        state=CreateListDialog.add_option
    ),
    Window(
        I18NFormat("tasklist-settings-msg", name=Format("{name}")),
        SwitchTo(I18NFormat("tasklist-settings-rename-btn"), id="switch_to_rename", state=CreateListDialog.change_name),
        SwitchTo(Const("<-"), id="to_main", state=CreateListDialog.main),
        state=CreateListDialog.settings
    ),
    Window(
        I18NFormat("tasklist-settings-rename-msg", name=Format("{name}")),
        TextInput(id="name_input", filter=F.text.len() <= 128, on_success=rename_tasklist),
        Back(Const("<-")),
        state=CreateListDialog.change_name
    ),
    Window(
        I18NFormat("tasklist-done", name=Format("{name}")),
        CopyButton(Const("share"), id="share_button", copy_text=Format("{share}")),
        state=CreateListDialog.done,
        getter=share_getter
    ),
    getter=getter
)
