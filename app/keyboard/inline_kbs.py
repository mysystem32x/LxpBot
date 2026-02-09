# inline_kbs.py - инлайн клавиатуры для сообщений.
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# - первоначальная кнопка
def start_command():
    btn = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Начать", callback_data="start")]
    ])
    return btn

# - кнопки "Личного кабинета"
def buttons_account():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📆 Расписания", callback_data="schedule"),
                InlineKeyboardButton(text="📂 Список заданий", callback_data="tasks")
            ],
            [
                InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"),
                InlineKeyboardButton(text="⛔️ Выйти", callback_data="logout")
            ]
        ]
    )

