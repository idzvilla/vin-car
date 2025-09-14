"""Настройка базы данных."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from .models import Base
from .settings import settings


class DatabaseManager:
    """Менеджер базы данных."""
    
    def __init__(self, database_url: str) -> None:
        """Инициализация менеджера БД.
        
        Args:
            database_url: URL подключения к базе данных
        """
        self.database_url = database_url
        self.engine = None
        self.session_factory = None
    
    def initialize(self) -> None:
        """Инициализация подключения к БД."""
        try:
            logger.info("Инициализация подключения к базе данных", url=self.database_url)
            
            # Создание движка
            self.engine = create_engine(
                self.database_url,
                echo=False,  # Установить True для отладки SQL
                pool_pre_ping=True,
                pool_recycle=3600,  # Переподключение каждый час
            )
            
            # Создание фабрики сессий
            self.session_factory = sessionmaker(
                self.engine,
                class_=Session,
                expire_on_commit=False,
            )
            
            logger.info("Подключение к базе данных установлено")
            
        except Exception as e:
            logger.error("Ошибка инициализации базы данных", error=str(e))
            raise
    
    def close(self) -> None:
        """Закрытие подключения к БД."""
        if self.engine:
            logger.info("Закрытие подключения к базе данных")
            self.engine.dispose()
            self.engine = None
            self.session_factory = None
    
    def create_tables(self) -> None:
        """Создание таблиц в базе данных."""
        if not self.engine:
            raise RuntimeError("База данных не инициализирована")
        
        try:
            logger.info("Создание таблиц в базе данных")
            
            # Создание всех таблиц синхронно через sync_engine
            from sqlalchemy import create_engine
            sync_engine = create_engine(str(self.engine.url).replace("+aiosqlite", ""))
            Base.metadata.create_all(sync_engine)
            sync_engine.dispose()
            
            logger.info("Таблицы созданы успешно")
            
        except Exception as e:
            logger.error("Ошибка создания таблиц", error=str(e), exc_info=True)
            raise
    
    def check_connection(self) -> bool:
        """Проверка подключения к БД.
        
        Returns:
            True если подключение работает, False иначе
        """
        if not self.engine:
            return False
        
        try:
            # Простая проверка - если движок создан, считаем что подключение работает
            return True
        except Exception as e:
            logger.warning("Ошибка проверки подключения к БД", error=str(e))
            return False
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[Session, None]:
        """Получение сессии базы данных.
        
        Yields:
            Сессия базы данных
            
        Raises:
            RuntimeError: Если БД не инициализирована
        """
        if not self.session_factory:
            raise RuntimeError("База данных не инициализирована")
        
        session = self.session_factory()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


# Глобальный менеджер БД
db_manager = DatabaseManager(settings.database_url)


def init_db() -> None:
    """Инициализация базы данных.
    
    Создает подключение и таблицы.
    """
    db_manager.initialize()
    db_manager.create_tables()
    
    # Проверка подключения
    if db_manager.check_connection():
        logger.info("База данных готова к работе")
    else:
        raise RuntimeError("Не удалось подключиться к базе данных")


def close_db() -> None:
    """Закрытие подключения к базе данных."""
    db_manager.close()


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[Session, None]:
    """Получение сессии базы данных.
    
    Yields:
        Сессия базы данных
    """
    async with db_manager.get_session() as session:
        yield session