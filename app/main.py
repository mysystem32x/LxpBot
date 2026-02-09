import asyncio
import logging
from aiogram import Bot, Dispatcher
from tortoise import Tortoise

# Импорт роутеров
from handlers.start import starter
from handlers.logout import leave
from handlers.scheduler import schedulerlist
from handlers.task_list import tasklist
from handlers.settings import setting_user

# Импорт сервиса напоминаний
from services.reminders import init_reminder_service, check_deadlines

TOKEN = "8407287434:AAHGLrMvurhEHE456sNVKnZZ_bd_6XKzRyo"

async def init_db():
    """Инициализация базы данных"""
    await Tortoise.init(
        db_url='sqlite://db.sqlite3',
        modules={'models': ['db.models']}
    )
    await Tortoise.generate_schemas()
    logging.info("✅ База данных инициализирована")

async def close_db():
    """Закрытие соединений с БД"""
    await Tortoise.close_connections()
    logging.info("✅ Соединения с БД закрыты")

async def on_startup():
    """Действия при запуске бота"""
    logging.info("🤖 Бот запускается...")

async def on_shutdown():
    """Действия при выключении бота"""
    logging.info("🤖 Бот выключается...")

async def main():
    # Инициализация БД
    await init_db()
   # await Tortoise.generate_schemas(safe=False)  # force update
    
    # Создаем бота и диспетчер
    bot = Bot(TOKEN)
    dp = Dispatcher()
    
    # Инициализируем сервис напоминаний ДО регистрации роутеров
    init_reminder_service(bot)
    
    # Регистрируем роутеры
    dp.include_router(starter)
    dp.include_router(leave)
    dp.include_router(schedulerlist)
    dp.include_router(tasklist)
    dp.include_router(setting_user)
    
    # Запускаем сервис напоминаний в фоне
    asyncio.create_task(check_deadlines())
    
    # Регистрируем startup и shutdown handlers
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    try:
        # Запускаем бота
        logging.info("🚀 Бот запущен и готов к работе!")
        await dp.start_polling(bot, skip_updates=True)
        
    except Exception as e:
        logging.error(f"❌ Критическая ошибка: {e}")
        
    finally:
        # Всегда закрываем соединения с БД
        await close_db()

if __name__ == "__main__":
    # Настраиваем логирование
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Запускаем главную функцию
    asyncio.run(main())