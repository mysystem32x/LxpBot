from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def start_command():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Начать", callback_data="start")]
    ])

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

def back_to_profile():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад в профиль", callback_data="profile")]
        ]
    )

def back_to_main():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="profile")]
        ]
    )
