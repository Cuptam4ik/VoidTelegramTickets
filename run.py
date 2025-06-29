#!/usr/bin/env python3
"""
Скрипт для запуска Telegram бота системы тикетов
"""
import sys
import os
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from handlers import user, admin, common

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Проверить наличие необходимых зависимостей"""
    try:
        import aiogram
        import aiosqlite
        logger.info("✅ Все зависимости установлены")
        return True
    except ImportError as e:
        logger.error(f"❌ Отсутствует зависимость: {e}")
        logger.info("Установите зависимости: pip install -r requirements.txt")
        return False

def check_config():
    """Проверить конфигурацию"""
    try:
        from config import API_TOKEN, ADMINS
        if not API_TOKEN or API_TOKEN == 'YOUR_BOT_TOKEN_HERE':
            logger.error("❌ Не установлен токен бота в config.py")
            return False
        if not ADMINS:
            logger.warning("⚠️ Список администраторов пуст")
        logger.info("✅ Конфигурация проверена")
        return True
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта конфигурации: {e}")
        return False

async def main():
    """Главная функция запуска бота"""
    # Инициализация бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Регистрация роутеров
    dp.include_router(user.router)
    dp.include_router(admin.router)
    dp.include_router(common.router)
    
    logger.info("🚀 Запуск бота...")
    
    # Удаляем вебхук и запускаем поллинг
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

def main_sync():
    """Синхронная обертка для запуска"""
    if not check_dependencies():
        sys.exit(1)
    
    if not check_config():
        sys.exit(1)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️ Бот остановлен")
    except Exception as e:
        logger.error(f"❌ Ошибка запуска: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main_sync() 