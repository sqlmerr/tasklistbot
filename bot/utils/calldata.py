from aiogram.filters.callback_data import CallbackData


class OptionClickData(CallbackData, prefix="option_click"):
    list_id: str
    option_index: int
