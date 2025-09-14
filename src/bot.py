"""Основной файл Telegram бота."""

from __future__ import annotations

import asyncio
import signal
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from loguru import logger

from .db import close_db, init_db
from .handlers import callbacks, manager, user
from .settings import settings


class VINReportBot:
    """Основной класс Telegram бота для обработки VIN отчетов."""
    
    def __init__(self) -> None:
        """Инициализация бота."""
        self.bot: Optional[Bot] = None
        self.dispatcher: Optional[Dispatcher] = None
        self._shutdown_event = asyncio.Event()
    
    async def initialize(self) -> None:
        """Инициализация бота и всех компонентов."""
        try:
            logger.info("Инициализация VIN Report Bot")
            
            # Настройка логирования
            self._setup_logging()
            
            # Инициализация базы данных
            from src.db_adapter import db_adapter
            await db_adapter.initialize()
            
            # Создание бота
            self.bot = Bot(
                token=settings.bot_token,
                default=DefaultBotProperties(
                    parse_mode=ParseMode.HTML
                )
            )
            
            # Создание диспетчера
            self.dispatcher = Dispatcher()
            
            # Регистрация роутеров
            self._register_routers()
            
            # Настройка обработчиков сигналов
            self._setup_signal_handlers()
            
            logger.info("VIN Report Bot инициализирован успешно")
            
        except Exception as e:
            logger.error("Ошибка инициализации бота", error=str(e), exc_info=True)
            raise
    
    async def start(self) -> None:
        """Запуск бота."""
        if not self.bot or not self.dispatcher:
            raise RuntimeError("Бот не инициализирован")
        
        try:
            logger.info("Запуск VIN Report Bot")
            
            # Проверяем доступность чата менеджеров
            try:
                chat_info = await self.bot.get_chat(settings.manager_chat_id)
                logger.info(f"✅ Чат менеджеров доступен: {chat_info.title} (ID: {settings.manager_chat_id})")
            except Exception as e:
                logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: Чат менеджеров недоступен (ID: {settings.manager_chat_id})", 
                            error=str(e))
                logger.error("Бот запущен, но заявки не будут отправляться в группу менеджеров!")
            
            # Получение информации о боте
            bot_info = await self.bot.get_me()
            logger.info(
                "Бот запущен",
                username=bot_info.username,
                first_name=bot_info.first_name,
                id=bot_info.id
            )
            
            # Запуск polling
            await self.dispatcher.start_polling(
                self.bot,
                allowed_updates=["message", "callback_query"],
                handle_as_tasks=True
            )
            
        except Exception as e:
            logger.error("Ошибка запуска бота", error=str(e))
            raise
    
    async def stop(self) -> None:
        """Остановка бота."""
        logger.info("Остановка VIN Report Bot")
        
        # Установка флага остановки
        self._shutdown_event.set()
        
        # Закрытие базы данных
        await close_db()
        
        # Остановка бота
        if self.bot:
            await self.bot.session.close()
        
        logger.info("VIN Report Bot остановлен")
    
    def _setup_logging(self) -> None:
        """Настройка логирования."""
        # Удаление стандартного обработчика
        logger.remove()
        
        # Добавление консольного обработчика
        logger.add(
            sys.stderr,
            level=settings.log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                   "<level>{message}</level>",
            colorize=True
        )
        
        # Добавление файлового обработчика
        logger.add(
            "logs/bot.log",
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            rotation="1 day",
            retention="30 days",
            compression="zip"
        )
        
        logger.info("Логирование настроено", level=settings.log_level)
    
    def _register_routers(self) -> None:
        """Регистрация роутеров обработчиков."""
        if not self.dispatcher:
            raise RuntimeError("Диспетчер не инициализирован")
        
        # Регистрация роутеров
        self.dispatcher.include_router(user.user_router)
        self.dispatcher.include_router(manager.manager_router)
        self.dispatcher.include_router(callbacks.callback_router)
        
        logger.info("Роутеры зарегистрированы")
    
    def _setup_signal_handlers(self) -> None:
        """Настройка обработчиков сигналов для graceful shutdown."""
        def signal_handler(signum: int, frame: object) -> None:
            """Обработчик сигнала."""
            logger.info("Получен сигнал остановки", signal=signum)
            self._shutdown_event.set()
        
        # Регистрация обработчиков сигналов
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def wait_for_shutdown(self) -> None:
        """Ожидание сигнала остановки."""
        await self._shutdown_event.wait()


@asynccontextmanager
async def bot_lifecycle() -> AsyncGenerator[VINReportBot, None]:
    """Контекстный менеджер для жизненного цикла бота.
    
    Yields:
        Экземпляр бота
    """
    bot = VINReportBot()
    
    try:
        await bot.initialize()
        yield bot
    finally:
        await bot.stop()


async def main() -> None:
    """Главная функция запуска бота."""
    try:
        async with bot_lifecycle() as bot:
            # Запуск бота в фоновой задаче
            bot_task = asyncio.create_task(bot.start())
            
            # Ожидание сигнала остановки
            await bot.wait_for_shutdown()
            
            # Отмена задачи бота
            bot_task.cancel()
            
            try:
                await bot_task
            except asyncio.CancelledError:
                pass
            
    except KeyboardInterrupt:
        logger.info("Получен сигнал прерывания")
    except Exception as e:
        logger.error("Критическая ошибка", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    # Создание директории для логов
    import os
    os.makedirs("logs", exist_ok=True)
    
    # Запуск бота
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error("Ошибка запуска", error=str(e))
        sys.exit(1)
