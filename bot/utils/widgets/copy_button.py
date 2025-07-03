from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Keyboard
from aiogram_dialog.widgets.text import Text
from aiogram_dialog.widgets.common import WhenCondition
from aiogram_dialog.api.internal import RawKeyboard, TextWidget
from aiogram.types import CopyTextButton, InlineKeyboardButton


class CopyButton(Keyboard):
    def __init__(
        self,
        text: Text,
        id: str,
        copy_text: str | TextWidget,
        when: WhenCondition = None,
    ):
        self.text = text
        self.copy_text = copy_text
        super().__init__(id, when)

    async def _render_keyboard(self, data: dict, manager: DialogManager) -> RawKeyboard:
        text = (
            self.copy_text
            if isinstance(self.copy_text, str)
            else await self.copy_text.render_text(data, manager)
        )
        return [
            [
                InlineKeyboardButton(
                    text=await self.text.render_text(data, manager),
                    copy_text=CopyTextButton(text=text),
                )
            ]
        ]
