from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def start_command():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Начать", callback_data="start")]
    ])

def buttons_account(user_id: int = None):
    # ID администратора для отображения кнопки
    ADMIN_IDS = [8039700599]
    
    keyboard = [
        [
            InlineKeyboardButton(text="📆 Расписания", callback_data="schedule"),
            InlineKeyboardButton(text="📂 Список заданий", callback_data="tasks")
        ],
        [
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"),
            InlineKeyboardButton(text="⛔️ Выйти", callback_data="logout")
        ]
    ]
    
    # Добавляем кнопку админки, если это админ
    if user_id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton(text="🛠 Админ-панель", callback_data="admin_start")])
        
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

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
