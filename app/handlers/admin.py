from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from db.models import User
import logging
import os

admin_router = Router()

# Список ID администраторов (можно добавить ID пользователя)
ADMIN_IDS = [8039700599] # ID владельца

# Файл-флаг для отключения бота (простая реализация "выключения")
MAINTENANCE_FILE = "maintenance.flag"

def is_admin(user_id: int):
    return user_id in ADMIN_IDS

@admin_router.callback_query(F.data == "admin_start")
async def admin_start_callback(call: CallbackQuery):
    await admin_panel(call.message, call.from_user.id)
    await call.answer()

@admin_router.message(Command("admin"))
async def admin_command(message: Message):
    await admin_panel(message, message.from_user.id)

async def admin_panel(message: Message, user_id: int):
    if not is_admin(user_id):
        return

    users_count = await User.all().count()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Список участников", callback_data="admin_users")],
        [InlineKeyboardButton(text="📜 Логи (последние 10)", callback_data="admin_logs")],
        [InlineKeyboardButton(text="🛑 Выключить/Включить бота", callback_data="admin_toggle_bot")],
        [InlineKeyboardButton(text="🏠 Выход", callback_data="profile")]
    ])
    
    status = "🔴 ВЫКЛЮЧЕН (Техработы)" if os.path.exists(MAINTENANCE_FILE) else "🟢 РАБОТАЕТ"
    
    await message.answer(
        f"🛠 <b>АДМИН-ПАНЕЛЬ</b>\n\n"
        f"📊 Всего пользователей: <b>{users_count}</b>\n"
        f"🤖 Статус бота: <b>{status}</b>",
        parse_mode="HTML",
        reply_markup=keyboard
    )

@admin_router.callback_query(F.data == "admin_users")
async def admin_list_users(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("Доступ запрещен", show_alert=True)
        return
    
    users = await User.all().order_by("-id").limit(20)
    text = "👥 <b>ПОСЛЕДНИЕ 20 УЧАСТНИКОВ:</b>\n\n"
    
    for u in users:
        role = "🎓" if u.role == "STUDENT" else "👨‍🏫"
        text += f"{role} {u.firstName or ''} {u.lastName or ''} (@{u.telegram_id})\n"
        text += f"   📧 {u.email}\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")]])
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)

@admin_router.callback_query(F.data == "admin_logs")
async def admin_show_logs(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    
    # Пытаемся прочитать последние строки лога (если он пишется в файл)
    # В данном случае просто имитируем или читаем системный лог если он есть
    log_text = "📜 <b>ПОСЛЕДНИЕ ЛОГИ:</b>\n\n<code>"
    try:
        # Если бот запущен через nohup или перенаправляет лог в файл bot.log
        if os.path.exists("bot.log"):
            with open("bot.log", "r") as f:
                lines = f.readlines()
                log_text += "".join(lines[-10:])
        else:
            log_text += "Файл bot.log не найден. Логи выводятся в консоль."
    except Exception as e:
        log_text += f"Ошибка чтения логов: {e}"
    
    log_text += "</code>"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")]])
    await call.message.edit_text(log_text, parse_mode="HTML", reply_markup=keyboard)

@admin_router.callback_query(F.data == "admin_toggle_bot")
async def admin_toggle_bot(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    
    if os.path.exists(MAINTENANCE_FILE):
        os.remove(MAINTENANCE_FILE)
        await call.answer("Бот включен", show_alert=True)
    else:
        with open(MAINTENANCE_FILE, "w") as f:
            f.write("on")
        await call.answer("Бот переведен в режим техработ", show_alert=True)
    
    await admin_panel(call.message, call.from_user.id)
    await call.message.delete()

@admin_router.callback_query(F.data == "admin_back")
async def admin_back(call: CallbackQuery):
    await admin_panel(call.message, call.from_user.id)
    await call.message.delete()

# Middleware для проверки режима техработ
async def maintenance_middleware(handler, event, data):
    user_id = event.from_user.id
    if os.path.exists(MAINTENANCE_FILE) and not is_admin(user_id):
        if isinstance(event, Message):
            await event.answer("⚠️ Бот временно отключен администратором на техническое обслуживание.")
        elif isinstance(event, CallbackQuery):
            await event.answer("⚠️ Бот временно отключен.", show_alert=True)
        return
    return await handler(event, data)
