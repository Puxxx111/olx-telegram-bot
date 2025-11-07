from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def main_menu(tracking_running: bool) -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="🗃️ Мої фiльтри")],
        [KeyboardButton(text="📡 Відстежити фільтр")],
    ]
    if tracking_running:
        buttons.append([KeyboardButton(text="⏹ Зупинити!")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def filters_menu(names: list[str]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(
        text=name, callback_data=f"filter:{name}")] for name in names]
    rows.append([InlineKeyboardButton(
        text="💾 Створити фільтр", callback_data="filters:create")])
    if names:
        rows.append([InlineKeyboardButton(
            text="🗑 Видалити фільтр", callback_data="filters:delete")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def filters_delete_menu(names: list[str]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(
        text=f"🗑 Видалити: {name}", callback_data=f"filters:delete:{name}")] for name in names]
    return InlineKeyboardMarkup(inline_keyboard=rows or [[InlineKeyboardButton(text="👐 Фільтри ще не створені", callback_data="noop")]])


def tracking_choice_menu(names: list[str]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(
        text=name, callback_data=f"track:{name}")] for name in names]
    if not names:
        rows.append([InlineKeyboardButton(
            text="💾 Створити фільтр", callback_data="filters:create")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def tracking_start_menu(filter_name: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Запустити!",
                              callback_data=f"track:start:{filter_name}")]
    ])
