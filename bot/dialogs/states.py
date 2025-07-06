from aiogram.fsm.state import StatesGroup, State


class CreateListDialog(StatesGroup):
    main = State()
    add_option = State()
    delete_confirm = State()
    done = State()


class EditListSettingsDialog(StatesGroup):
    main = State()
    change_name = State()
    edit_security = State()
    security_permission_menu = State()


class ListViewerDialog(StatesGroup):
    main = State()
    edit_mode = State()
    edit_mode_menu = State()
    edit_mode_rename = State()
    delete_mode = State()
