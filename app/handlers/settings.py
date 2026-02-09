from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram import Router, F
from db.utils import get_user_settings, toggle_setting

setting_user = Router()

def get_settings_text(user_settings: dict) -> str:
    """Формирует текст настроек с эмодзи"""
    def bool_to_emoji(value: bool) -> str:
        return "✅" if value else "❌"
    
    return f"""
⚙️ <b>Настройки пользователя</b>

📢 <b>Уведомления:</b>
{bool_to_emoji(user_settings['reminders_enabled'])} Включить/выключить все
{bool_to_emoji(user_settings['remind_24h'])} За 24 часа до дедлайна
{bool_to_emoji(user_settings['remind_3h'])} За 3 часа до дедлайна  
{bool_to_emoji(user_settings['remind_1h'])} За 1 час до дедлайна

📅 <b>Ежедневные:</b>
{bool_to_emoji(user_settings['remind_daily'])} Ежедневный обзор заданий
"""

def get_settings_keyboard(user_settings: dict) -> InlineKeyboardMarkup:
    """Создает клавиатуру настроек"""
    buttons = [
        [
            InlineKeyboardButton(
                text=f"{'🔕' if user_settings['reminders_enabled'] else '🔔'} Все уведомления",
                callback_data="toggle_reminders_enabled"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{'✅' if user_settings['remind_24h'] else '❌'} За 24ч",
                callback_data="toggle_remind_24h"
            ),
            InlineKeyboardButton(
                text=f"{'✅' if user_settings['remind_3h'] else '❌'} За 3ч",
                callback_data="toggle_remind_3h"
            ),
            InlineKeyboardButton(
                text=f"{'✅' if user_settings['remind_1h'] else '❌'} За 1ч",
                callback_data="toggle_remind_1h"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{'📅' if user_settings['remind_daily'] else '📅'} Ежедневно",
                callback_data="toggle_remind_daily"
            )
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@setting_user.callback_query(F.data == "settings")
async def show_settings(call: CallbackQuery):
    from db.models import User
    
    # Находим пользователя
    user = await User.get_or_none(telegram_id=call.from_user.id)
    
    if not user:
        await call.answer("❌ Сначала зарегистрируйтесь через /start")
        return
    
    # ПЕРЕДАВАЙ user.id, а не call.from_user.id!
    user_settings = await get_user_settings(user.id)  # ← ВОТ ТУТ ИСПРАВЬ!
    
    text = get_settings_text(user_settings)
    keyboard = get_settings_keyboard(user_settings)
    
    await call.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    await call.answer()
# Обработчики переключения настроек
@setting_user.callback_query(F.data.startswith("toggle_"))
async def toggle_user_setting(call: CallbackQuery):
    """Переключает настройку"""
    from db.models import User
    
    # 1. Находим пользователя в БД
    user = await User.get_or_none(telegram_id=call.from_user.id)
    if not user:
        await call.answer("❌ Пользователь не найден")
        return
    
    # 2. Получаем название настройки
    setting_name = call.data.replace("toggle_", "")
    
    # 3. Переключаем настройку - передаем user.id!
    new_value = await toggle_setting(user.id, setting_name)
    
    # 4. Получаем обновленные настройки - передаем user.id!
    user_settings = await get_user_settings(user.id)
    
    # 5. Обновляем сообщение
    text = get_settings_text(user_settings)
    keyboard = get_settings_keyboard(user_settings)
    
    await call.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await call.answer(f"Настройка изменена: {'Включено' if new_value else 'Выключено'}")