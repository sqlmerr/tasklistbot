from typing import Any, TypedDict
from aiogram import F
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, SwitchTo, ListGroup, Back, Row, SwitchInlineQuery
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
    delete_confirm = State()


async def show_alert(c: CallbackQuery, _: Button, manager: DialogManager):
    await c.answer("❗️ Test", show_alert=True, cache_time=0)
    await c.message.delete()
    await manager.done()


async def getter(dialog_manager: DialogManager, **kwargs) -> dict:
    name = dialog_manager.dialog_data.get("name", "Task list")
    options: list[str] = dialog_manager.dialog_data.get("options", [])
    mode = dialog_manager.dialog_data.get("mode", "none")
    return {
        "name": name,
        "options": [{"id": i, "content": o} for i, o in enumerate(options)],
        "can_be_completed": len(options) > 0,
        "mode": mode,
    }


async def share_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    share = dialog_manager.dialog_data.get("share")
    return {"share": share}


async def create_option(
    message: Message, widget: Any, dialog_manager: DialogManager, data: str
):
    options: list[str] = dialog_manager.dialog_data.get("options", [])
    options.append(data)
    dialog_manager.dialog_data["options"] = options
    await dialog_manager.switch_to(CreateListDialog.main)


async def rename_tasklist(
    message: Message, widget: Any, dialog_manager: DialogManager, data: str
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
        options=[TaskOption(name=o, completed=False) for o in options],
    )
    await tasklist.insert()
    bot_username = (await callback.bot.me()).username
    share = f"open:{tasklist.id}"
    manager.dialog_data["share"] = share
    await manager.switch_to(CreateListDialog.done)

async def enter_delete_mode(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await callback.answer()
    manager.dialog_data["mode"] = "delete"

async def quit_delete_mode(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await callback.answer()
    manager.dialog_data["mode"] = "none"

async def option_button_click(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await callback.answer()
    if manager.dialog_data.get("mode", "none") == "delete":
        manager.dialog_data["deleting_option"] = manager.item_id
        await manager.switch_to(CreateListDialog.delete_confirm)

async def confirm_delete(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await callback.answer()
    index = int(manager.dialog_data["deleting_option"])
    options: list[str] = manager.dialog_data.get("options", [])
    options.pop(index)
    manager.dialog_data["options"] = options
    manager.dialog_data.pop("deleting_option")
    await manager.switch_to(CreateListDialog.main)


ui = Dialog(
    Window(
        I18NFormat("tasklist-menu-msg", name=Format("{name}")),
        I18NFormat("tasklist-menu-delete-mode-msg", when=F["mode"] == "delete"),
        ListGroup(
            Button(Format("{item[id]}. {item[content]}"), id="option_button", on_click=option_button_click),
            id="options_list",
            items="options",
            item_id_getter=lambda item: item["id"],
        ),
        Row(
            SwitchTo(Const("+"), id="add_option", state=CreateListDialog.add_option, when=F["mode"] == "none"),
            Button(Const("🗑️"), id="enter_delete_mode", on_click=enter_delete_mode, when=F["mode"] == "none"),
            Button(Const("✅"), id="quit_delete_mode", on_click=quit_delete_mode, when=F["mode"] == "delete"),
        ),
        Row(
            SwitchTo(
                I18NFormat("tasklist-settings-btn"),
                id="switch_to_settings",
                state=CreateListDialog.settings,
            ),
            Button(Const("done"), id="done", on_click=done, when=F["can_be_completed"] & F["mode"] == "none"),
        ),
        state=CreateListDialog.main,
    ),
    Window(
        I18NFormat("tasklist-option-create-msg"),
        TextInput(
            id="option_input", filter=F.text.len() <= 32, on_success=create_option
        ),
        Back(Const("<-")),
        state=CreateListDialog.add_option,
    ),
    Window(
        I18NFormat("tasklist-settings-msg", name=Format("{name}")),
        SwitchTo(
            I18NFormat("tasklist-settings-rename-btn"),
            id="switch_to_rename",
            state=CreateListDialog.change_name,
        ),
        SwitchTo(Const("<-"), id="to_main", state=CreateListDialog.main),
        state=CreateListDialog.settings,
    ),
    Window(
        I18NFormat("tasklist-settings-rename-msg", name=Format("{name}")),
        TextInput(
            id="name_input", filter=F.text.len() <= 128, on_success=rename_tasklist
        ),
        Back(Const("<-")),
        state=CreateListDialog.change_name,
    ),
    Window(
        I18NFormat("tasklist-done", name=Format("{name}")),
        # CopyButton(Const("share"), id="share_button", copy_text=Format("{share}")),
        SwitchInlineQuery(Const("share"), switch_inline_query=Format("{share}")),
        state=CreateListDialog.done,
        getter=share_getter,
    ),
    Window(
        I18NFormat("tasklist-confirm-delete"),
        Back(),
        Button(I18NFormat("confirm-btn"), id="confirm_delete_btn", on_click=confirm_delete),
        state=CreateListDialog.delete_confirm
    ),
    getter=getter,
)
