import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from database import Database
from constants import BOT_TOKEN
from handlers import common, admin, superadmin, student
from notifications import init_notification_service
from scheduler import init_scheduler

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Главная функция запуска бота"""
    try:
        # Инициализация бота и диспетчера
        bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        # Инициализация базы данных
        await Database.init_db()
        logger.info("✅ База данных инициализирована")
        
        # Инициализация сервисов
        init_notification_service(bot)
        scheduler = init_scheduler(bot)
        
        # Регистрация роутеров
        dp.include_router(common.router)
        dp.include_router(admin.router)
        dp.include_router(superadmin.router)
        dp.include_router(student.router)
        
        logger.info("✅ Роутеры зарегистрированы")
        
        # Запуск планировщика в фоне
        scheduler_task = asyncio.create_task(scheduler.start())
        
        # Запуск бота
        logger.info("🚀 Запуск бота...")
        try:
            await dp.start_polling(bot)
        finally:
            # Остановка планировщика при завершении
            await scheduler.stop()
            scheduler_task.cancel()
            await Database.close()
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Ошибка запуска: {e}")
