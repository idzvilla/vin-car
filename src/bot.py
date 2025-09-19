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

from .db import close_db
from .handlers import callbacks, manager, user
from .settings import settings


class VINReportBot:
    def __init__(self) -> None:
        self.bot: Optional[Bot] = None
        self.dispatcher: Optional[Dispatcher] = None
        self._shutdown_event = asyncio.Event()
    
    async def initialize(self) -> None:
        try:
            logger.info("Инициализация VIN Report Bot")
            
            self._setup_logging()
            logger.debug("Логирование настроено")
            
            from src.db_adapter import db_adapter
            await db_adapter.initialize()
            logger.debug("База данных инициализирована")
            
            # Инициализируем db_manager для PaymentService
            from src.db import init_db
            init_db()
            logger.debug("DB manager инициализирован")
            
            try:
                logger.debug(f"Создание бота с токеном: {settings.bot_token[:10]}...")
                self.bot = Bot(token=settings.bot_token)
                logger.debug("Бот создан")
            except Exception as e:
                logger.error("Ошибка создания бота", error=str(e), exc_info=True)
                raise
            
            self.dispatcher = Dispatcher()
            logger.debug("Диспетчер создан")
            
            self._register_routers()
            logger.debug("Роутеры зарегистрированы")
            
            self._setup_signal_handlers()
            logger.debug("Обработчики сигналов настроены")
            
            logger.info("VIN Report Bot инициализирован успешно")
            
        except Exception as e:
            logger.error("Ошибка инициализации бота", error=str(e), exc_info=True)
            raise
    
    async def start(self) -> None:
        if not self.bot or not self.dispatcher:
            raise RuntimeError("Бот не инициализирован")
        
        try:
            logger.info("Запуск VIN Report Bot")
            
            try:
                chat_info = await self.bot.get_chat(settings.manager_chat_id)
                logger.info(f"✅ Чат менеджеров доступен: {chat_info.title} (ID: {settings.manager_chat_id})")
            except Exception as e:
                logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: Чат менеджеров недоступен (ID: {settings.manager_chat_id})", 
                            error=str(e))
                logger.error("Бот запущен, но заявки не будут отправляться в группу менеджеров!")
            
            bot_info = await self.bot.get_me()
            logger.info(
                "Бот запущен",
                username=bot_info.username,
                first_name=bot_info.first_name,
                id=bot_info.id
            )
            
            await self.dispatcher.start_polling(
                self.bot,
                allowed_updates=["message", "callback_query"],
                handle_as_tasks=True
            )
            
        except Exception as e:
            logger.error("Ошибка запуска бота", error=str(e))
            raise
    
    async def stop(self) -> None:
        logger.info("Остановка VIN Report Bot")
        
        self._shutdown_event.set()
        
        await close_db()
        
        if self.bot:
            await self.bot.session.close()
        
        logger.info("VIN Report Bot остановлен")
    
    def _setup_logging(self) -> None:
        logger.remove()
        
        logger.add(
            sys.stderr,
            level=settings.log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                   "<level>{message}</level>",
            colorize=True
        )
        
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
        if not self.dispatcher:
            raise RuntimeError("Диспетчер не инициализирован")
        
        self.dispatcher.include_router(user.user_router)
        self.dispatcher.include_router(manager.manager_router)
        self.dispatcher.include_router(callbacks.callback_router)
        
        logger.info("Роутеры зарегистрированы")
    
    def _setup_signal_handlers(self) -> None:
        def signal_handler(signum: int, frame: object) -> None:
            logger.info("Получен сигнал остановки", signal=signum)
            self._shutdown_event.set()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def wait_for_shutdown(self) -> None:
        await self._shutdown_event.wait()


@asynccontextmanager
async def bot_lifecycle() -> AsyncGenerator[VINReportBot, None]:
    bot = VINReportBot()
    
    try:
        await bot.initialize()
        yield bot
    finally:
        await bot.stop()


async def main() -> None:
    try:
        async with bot_lifecycle() as bot:
            bot_task = asyncio.create_task(bot.start())
            
            await bot.wait_for_shutdown()
            
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
    import os
    os.makedirs("logs", exist_ok=True)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error("Ошибка запуска", error=str(e))
        sys.exit(1)
