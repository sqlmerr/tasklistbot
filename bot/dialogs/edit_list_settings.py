from typing import Any

from aiogram import F
from aiogram.types import CallbackQuery, Message

from aiogram_dialog.widgets.kbd import (
    Back,
    SwitchTo,
    Button,
    ListGroup,
    Toggle,
    ManagedRadio,
)
from aiogram_dialog.widgets.text import Format, Const
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog import Dialog, DialogManager, Window, ChatEvent
from .states import EditListSettingsDialog, CreateListDialog

from bot.utils.widgets.i18n_format import I18NFormat
from bot.db.models import SecurityRuleTypes, SecurityPermissions, SecurityRuleType


async def on_start(data: dict, manager: DialogManager):
    manager.dialog_data.update(data)
    print()


async def done(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.answer()

    await manager.start(CreateListDialog.main, data=manager.dialog_data)


async def rename_tasklist(
    message: Message, widget: Any, dialog_manager: DialogManager, data: str
):
    dialog_manager.dialog_data["name"] = data
    await dialog_manager.switch_to(EditListSettingsDialog.main)


async def getter(dialog_manager: DialogManager, **kwargs) -> dict:
    name = dialog_manager.dialog_data.get("name", "Task list")
    return {"name": name, "dialog_data": dialog_manager.dialog_data}


def edit_security(perm: str):
    async def wrapper(
        callback: CallbackQuery, btn: Button, manager: DialogManager
    ) -> None:
        await callback.answer()
        manager.dialog_data["_editing_security_perm"] = perm
        rule = SecurityRuleType(
            manager.dialog_data.get("security", {})
            .get(perm, {})
            .get("rule_type", "owner")
        )
        widget: ManagedRadio = manager.find("rule_toggle")
        print(type(widget.get_checked()))
        await widget.set_checked(rule)
        print(type(widget.get_checked()))

        manager.dialog_data["_editing_security_perm_rule"] = str(rule)
        await manager.switch_to(EditListSettingsDialog.security_permission_menu)

    return wrapper


async def change_rule(
    callback: CallbackQuery, widget: Any, manager: DialogManager, data: str
) -> None:
    await callback.answer()
    perm = manager.dialog_data["_editing_security_perm"]
    security = manager.dialog_data.get("security", {})
    security[perm] = {"rule_type": data}
    if data == SecurityRuleType.SELECTED:
        security[perm]["users"] = []
    manager.dialog_data["security"] = security
    manager.dialog_data["_editing_security_perm_rule"] = data
    print(manager.dialog_data)


ui = Dialog(
    Window(
        I18NFormat("tasklist-settings-msg", name=Format("{name}")),
        SwitchTo(
            I18NFormat("tasklist-settings-rename-btn"),
            id="switch_to_rename",
            state=EditListSettingsDialog.change_name,
        ),
        SwitchTo(
            I18NFormat("tasklist-settings-security-btn"),
            id="switch_to_security",
            state=EditListSettingsDialog.edit_security,
        ),
        Button(Const("<-"), id="back", on_click=done),
        state=EditListSettingsDialog.main,
    ),
    Window(
        I18NFormat("tasklist-settings-rename-msg", name=Format("{name}")),
        TextInput(
            id="name_input", filter=F.text.len() <= 128, on_success=rename_tasklist
        ),
        Back(Const("<-")),
        state=EditListSettingsDialog.change_name,
    ),
    Window(
        I18NFormat("tasklist-settings-security-msg"),
        # ListGroup(
        #     Button(Format("{item}"), id="sec", on_click=edit_security),
        #     id="l",
        #     item_id_getter=lambda item: str(item),
        #     items=SecurityPermissions
        # ),
        Button(Format("read"), id="sec_read", on_click=edit_security("read")),
        Button(
            Format("mark_tasks_as_completed"),
            id="sec_mark_tasks_as_completed",
            on_click=edit_security("mark_tasks_as_completed"),
        ),
        Button(
            Format("add_new_tasks"),
            id="sec_add_new_tasks",
            on_click=edit_security("add_new_tasks"),
        ),
        Button(
            Format("edit_tasks"),
            id="sec_edit_tasks",
            on_click=edit_security("edit_tasks"),
        ),
        Button(
            Format("delete_tasks"),
            id="sec_delete_tasks",
            on_click=edit_security("delete_tasks"),
        ),
        SwitchTo(Const("<-"), id="back", state=EditListSettingsDialog.main),
        state=EditListSettingsDialog.edit_security,
    ),
    Window(
        I18NFormat("tasklist-settings-security-edit-permission-msg", perm=F["dialog_data"]["_editing_security_perm"]),
        Toggle(
            Format("{item}"),
            id="rule_toggle",
            item_id_getter=lambda item: item,
            items=SecurityRuleTypes,
            type_factory=lambda item: str(item),
            on_click=change_rule,
        ),
        Button(
            I18NFormat("tasklist-settings-security-selected-users-edit-btn"),
            id="update_selected_users",
            when=F["dialog_data"]["_editing_security_perm_rule"]
            == SecurityRuleType.SELECTED,
        ),
        Back(Const("<-")),
        state=EditListSettingsDialog.security_permission_menu,
    ),
    getter=getter,
    on_start=on_start,
)
