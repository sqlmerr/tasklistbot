from typing import Any
from aiogram import F
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, SwitchTo, ListGroup, SwitchInlineQuery, Row, Back
from aiogram_dialog.widgets.text import Format, Const, Multi, Case
from aiogram_dialog.widgets.input import TextInput

from bot.db.models import TaskList

from .states import ListViewerDialog
from bot.utils.widgets import I18NFormat
from bot.utils.permissions import ensure_user_has_permission


async def getter(dialog_manager: DialogManager, **kwargs) -> dict:
    tasklist_id = dialog_manager.dialog_data["tasklist_id"]
    is_unsaved = dialog_manager.dialog_data.get("is_unsaved")
    edited_options: list[dict] = dialog_manager.dialog_data.get("edited_options", [])
    tasklist = await TaskList.get(tasklist_id, fetch_links=True)
    if not tasklist:
        raise ValueError
    perms = {}
    for p in tasklist.security.model_dump().keys():
        perms[p] = ensure_user_has_permission(tasklist, dialog_manager.event.from_user.id, p)
    options = [{"name": o.name, "completed": o.completed, "i": i} for i, o in enumerate(tasklist.options)]
    for i in edited_options:
        options[i["i"]]["name"] = i["name"]

    return {
        "name": tasklist.title,
        "options": options,
        "dialog_data": dialog_manager.dialog_data,
        "tasklist_id": tasklist_id,
        "is_unsaved": is_unsaved,
        "perms": perms
    }

async def on_start(data: dict, dialog_manager: DialogManager) -> None:
    dialog_manager.dialog_data.update(data)
    if "tasklist_id" not in data:
        await dialog_manager.done()
        raise ValueError


async def rename_option(message: Message, widget: Any, dialog_manager: DialogManager, data: str) -> None:
    item_id = dialog_manager.dialog_data["_editing_option_id"]
    dialog_manager.dialog_data["is_unsaved"] = True
    edited_options: list[dict] = dialog_manager.dialog_data.get("edited_options", [])
    edited_options.append({"i": int(item_id), "name": data})
    dialog_manager.dialog_data["edited_options"] = edited_options

    await dialog_manager.switch_to(ListViewerDialog.edit_mode_menu)

async def start_editing(callback: CallbackQuery, button: Button, dialog_manager: DialogManager) -> None:
    dialog_manager.dialog_data["_editing_option_id"] = dialog_manager.item_id
    

async def save(callback: CallbackQuery, button: Button, dialog_manager: DialogManager) -> None:
    await callback.answer()
    tasklist_id = dialog_manager.dialog_data["tasklist_id"]
    edited_options: list[dict] = dialog_manager.dialog_data["edited_options"]

    tasklist = await TaskList.get(tasklist_id)
    if not tasklist:
        raise ValueError
    for option in edited_options:
        tasklist.options[option["i"]].name = option["name"]
    await tasklist.save()
    dialog_manager.dialog_data["is_unsaved"] = False

ui = Dialog(
    Window(
        I18NFormat("tasklist-menu-msg", name=F["name"]),
        ListGroup(
            Button(
                Multi(
                    Format("{item[i]}."),
                    Format("{item[name]}"),
                    Case(
                        {
                            True: Const("✅"),
                            False: Const(" ")
                        },
                        selector=F["item"]["completed"]
                    ),
                    sep=" ",
                ), 
                id="option",
            ),
            id="options",
            items="options",
            item_id_getter=lambda item: item["i"],
        ),
        Row(
            SwitchTo(Const("✏️"), id="to_edit_mode", state=ListViewerDialog.edit_mode, when=F["perms"]["edit_tasks"]),
            SwitchTo(Const("🗑️"), id="to_delete_mode", state=ListViewerDialog.delete_mode, when=F["perms"]["delete_tasks"]),
        ),
        Button(Const("save"), id="save_btn", on_click=save, when=F["is_unsaved"]),
        SwitchInlineQuery(Const("share"), switch_inline_query=Format("open:{tasklist_id}"), when=~F["is_unsaved"]),
        state=ListViewerDialog.main
    ),
    Window(
        I18NFormat("tasklist-menu-msg", name=F["name"]),
        I18NFormat("tasklist-menu-edit-mode-msg"),
        ListGroup(
            SwitchTo(
                Format("{item[i]}. {item[name]}"),
                state=ListViewerDialog.edit_mode_menu,
                on_click=start_editing,
                id="option_edit",
            ),
            id="options_to_edit",
            items="options",
            item_id_getter=lambda item: item["i"],
        ),
        Back(Const("<-")),
        state=ListViewerDialog.edit_mode
    ),
    Window(
        I18NFormat("tasklist-edit-menu-msg"),
        SwitchTo(I18NFormat("rename-btn"), id="rename", state=ListViewerDialog.edit_mode_rename),
        Back(Const("<-")),
        state=ListViewerDialog.edit_mode_menu
    ),
    Window(
        I18NFormat("tasklist-edit-menu-rename-msg"),
        TextInput(id="input", on_success=rename_option, filter=F.text.len() <= 32),
        Back(Const("<-")),
        state=ListViewerDialog.edit_mode_rename
    ),
    getter=getter,
    on_start=on_start
)