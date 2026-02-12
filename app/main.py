import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from tortoise import Tortoise
from aiohttp import web  # <-- ДОБАВЛЕНО

# Импорт роутеров
from handlers.start import starter
from handlers.logout import leave
from handlers.scheduler import schedulerlist
from handlers.task_list import tasklist
from handlers.settings import setting_user
from handlers.admin import admin_router, maintenance_middleware

# Импорт сервиса напоминаний
from services.reminders import init_reminder_service, check_deadlines

# ============================================
# ТОКЕН БЕРЕМ ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ
# ============================================
TOKEN = os.getenv("BOT_TOKEN", "8407287434:AAHGLrMvurhEHE456sNVKnZZ_bd_6XKzRyo")
if not TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в переменных окружения!")

# ============================================
# НАСТРОЙКА БАЗЫ ДАННЫХ (SQLite как было)
# ============================================
async def init_db():
    """Инициализация базы данных"""
    await Tortoise.init(
        db_url='sqlite://db.sqlite3',
        modules={'models': ['db.models']}
    )
    await Tortoise.generate_schemas()

async def close_db():
    """Закрытие соединений с БД"""
    await Tortoise.close_connections()
    logging.info("✅ Соединения с БД закрыты")

# ============================================
# ФИКТИВНЫЙ HTTP-СЕРВЕР ДЛЯ RENDER
# ============================================
async def handle_root(request):
    """Заглушка для Render"""
    return web.Response(text="🤖 Telegram Bot is running")

async def start_webserver():
    """Запускаем HTTP сервер на порту из окружения"""
    port = int(os.environ.get('PORT', 10000))
    
    app = web.Application()
    app.router.add_get('/', handle_root)
    app.router.add_get('/health', handle_root)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logging.info(f"🌐 HTTP сервер-заглушка запущен на порту {port}")

async def on_startup():
    """Действия при запуске бота"""
    logging.info("🤖 Бот запускается...")

async def on_shutdown():
    """Действия при выключении бота"""
    logging.info("🤖 Бот выключается...")

async def main():
    # Запускаем HTTP сервер для Render (ОБЯЗАТЕЛЬНО!)
    await start_webserver()
    
    # Инициализация БД
    await init_db()
    
    # Создаем бота и диспетчер
    bot = Bot(TOKEN)
    dp = Dispatcher()
    
    # Регистрация мидлвари для техработ
    dp.message.outer_middleware(maintenance_middleware)
    dp.callback_query.outer_middleware(maintenance_middleware)
    
    # Инициализируем сервис напоминаний ДО регистрации роутеров
    init_reminder_service(bot)
    
    # Регистрируем роутеры
    dp.include_router(admin_router)
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
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(),
        ]
    )
    
    # Запускаем главную функцию
    asyncio.run(main())
