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
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self.engine = None
        self.session_factory = None
    
    def initialize(self) -> None:
        try:
            logger.info("Инициализация подключения к базе данных", url=self.database_url)
            
            self.engine = create_engine(
                self.database_url,
                echo=False,
                pool_pre_ping=True,
                pool_recycle=3600,
            )
            
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
        if self.engine:
            logger.info("Закрытие подключения к базе данных")
            self.engine.dispose()
            self.engine = None
            self.session_factory = None
    
    def create_tables(self) -> None:
        if not self.engine:
            raise RuntimeError("База данных не инициализирована")
        
        try:
            logger.info("Создание таблиц в базе данных")
            
            from sqlalchemy import create_engine
            sync_engine = create_engine(str(self.engine.url).replace("+aiosqlite", ""))
            Base.metadata.create_all(sync_engine)
            sync_engine.dispose()
            
            logger.info("Таблицы созданы успешно")
            
        except Exception as e:
            logger.error("Ошибка создания таблиц", error=str(e), exc_info=True)
            raise
    
    def check_connection(self) -> bool:
        if not self.engine:
            return False
        
        try:
            return True
        except Exception as e:
            logger.warning("Ошибка проверки подключения к БД", error=str(e))
            return False
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[Session, None]:
        if not self.session_factory:
            raise RuntimeError("База данных не инициализирована")
        
        session = self.session_factory()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


db_manager = DatabaseManager(settings.database_url)


def init_db() -> None:
    db_manager.initialize()
    db_manager.create_tables()
    
    if db_manager.check_connection():
        logger.info("База данных готова к работе")
    else:
        raise RuntimeError("Не удалось подключиться к базе данных")


def close_db() -> None:
    db_manager.close()


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[Session, None]:
    async with db_manager.get_session() as session:
        yield session