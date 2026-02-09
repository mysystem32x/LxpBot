# ЗАМЕНИ весь файл на этот код:
import asyncio
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)

# Глобальная переменная для бота
_bot_instance = None

def init_reminder_service(bot):
    """Инициализирует сервис напоминаний с ботом"""
    global _bot_instance
    _bot_instance = bot
    logger.info("✅ Сервис напоминаний инициализирован")

async def get_user_tasks_from_api(user):
    """Получает задания пользователя через API"""
    try:
        from api.get_scheduler import get_tasks as api_get_tasks
        return await api_get_tasks(user.email, user.password, user.telegram_id)
    except Exception as e:
        logger.error(f"Ошибка получения заданий для пользователя {user.id}: {e}")
        return []

async def send_reminder(telegram_id: int, task: dict, reminder_type: str):
    """Отправляет одно напоминание"""
    global _bot_instance
    
    if not _bot_instance:
        logger.error("Бот не инициализирован!")
        return
        
    try:
        task_name = task["contentBlock"]["name"]
        discipline = task["topic"]["chapter"]["discipline"]["name"]
        deadline = task.get("taskDeadline")
        
        messages = {
            "24h": "🟡 <b>Напоминание за 24 часа!</b>",
            "3h": "🟠 <b>Срочно! Осталось 3 часа!</b>",
            "1h": "🔴 <b>Последний час! Срочно!</b>"
        }
        
        text = (
            f"{messages.get(reminder_type, '⏰ Напоминание')}\n\n"
            f"📌 <b>{task_name}</b>\n"
            f"📚 {discipline}\n"
        )
        
        if deadline:
            deadline_dt = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
            deadline_str = deadline_dt.strftime("%d.%m.%Y, %H:%M")
            text += f"⏰ <b>Дедлайн:</b> {deadline_str}\n"
        
        text += f"\nНе забудьте выполнить задание!"
        
        await _bot_instance.send_message(chat_id=telegram_id, text=text, parse_mode="HTML")
        logger.info(f"✅ Напоминание отправлено пользователю {telegram_id}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка отправки напоминания пользователю {telegram_id}: {e}")

async def send_reminder_if_needed(user, task, reminder_type):
    """Отправляет напоминание если еще не отправляли"""
    try:
        from db.models import SentReminder
        
        sent = await SentReminder.filter(
            user_id=user.id,
            task_id=task["contentBlock"]["id"],
            reminder_type=reminder_type
        ).exists()
        
        if not sent:
            await send_reminder(user.telegram_id, task, reminder_type)
            
            await SentReminder.create(
                user_id=user.id,
                task_id=task["contentBlock"]["id"],
                reminder_type=reminder_type
            )
            return True
    except Exception as e:
        logger.error(f"Ошибка отправки напоминания: {e}")
    return False

async def check_deadlines():
    """Фоновая задача: проверяет дедлайны каждые 30 минут"""
    global _bot_instance
    
    if not _bot_instance:
        logger.error("Бот не инициализирован! Сервис напоминаний не запущен.")
        return
    
    logger.info("⏰ Сервис напоминаний запущен")
    
    while True:
        try:
            logger.debug(f"🔍 Проверяю дедлайны... {datetime.now()}")
            
            from db.models import User
            from db.utils import get_user_settings
            
            users = await User.all()
            
            for user in users:
                try:
                    settings = await get_user_settings(user.id)
                    
                    if not settings['reminders_enabled']:
                        continue
                    
                    tasks = await get_user_tasks_from_api(user)
                    
                    for task in tasks:
                        deadline = task.get("taskDeadline")
                        if not deadline:
                            continue
                        
                        deadline_dt = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
                        now = datetime.now(timezone.utc)
                        time_left = deadline_dt - now
                        
                        if time_left.total_seconds() <= 0:
                            continue
                        
                        if (timedelta(hours=0) < time_left <= timedelta(hours=24) 
                            and settings['remind_24h']):
                            await send_reminder_if_needed(user, task, "24h")
                        
                        if (timedelta(hours=0) < time_left <= timedelta(hours=3) 
                            and settings['remind_3h']):
                            await send_reminder_if_needed(user, task, "3h")
                        
                        if (timedelta(hours=0) < time_left <= timedelta(hours=1) 
                            and settings['remind_1h']):
                            await send_reminder_if_needed(user, task, "1h")
                            
                except Exception as e:
                    logger.error(f"❌ Ошибка обработки пользователя {user.id}: {e}")
                    continue
            
            await asyncio.sleep(1800)
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка в сервисе напоминаний: {e}")
            await asyncio.sleep(300)