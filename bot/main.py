import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from bot.config import Config
from bot.database import Database
from bot.checker import WebsiteChecker
from bot.scheduler import MonitoringScheduler
from bot.handlers import router

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def set_bot_commands(bot: Bot):
    """Установка команд меню бота"""
    commands = [
        BotCommand(command="/start", description="Запустить бота"),
        BotCommand(command="/add", description="Добавить сайт"),
        BotCommand(command="/list", description="Список сайтов"),
        BotCommand(command="/stats", description="Статистика"),
        BotCommand(command="/delete", description="Удалить сайт")
    ]
    await bot.set_my_commands(commands)


from bot.middleware import DependenciesMiddleware


async def main():
    try:
        # Загрузка конфигурации
        config = Config()

        # Инициализация базы данных
        db = Database(config.db_url)
        print("База данных подключена успешно")

        # Инициализация проверщика
        checker = WebsiteChecker()

        # Создание бота и диспетчера
        bot = Bot(token=config.bot_token)
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)

        # Инициализация планировщика
        scheduler = MonitoringScheduler(bot, db, checker)

        # Создаем и регистрируем middleware
        dependencies_middleware = DependenciesMiddleware(db, checker, scheduler)
        dp.message.outer_middleware.register(dependencies_middleware)
        dp.callback_query.outer_middleware.register(dependencies_middleware)

        # Включаем роутер
        dp.include_router(router)

        # Устанавливаем команды бота
        await set_bot_commands(bot)

        # Запускаем планировщик
        await scheduler.start()

        # Запуск бота
        logger.info("Бот запущен!")
        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())