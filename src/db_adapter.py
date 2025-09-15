from __future__ import annotations

import asyncio
from typing import Optional, Dict, Any
from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from .models import Base
from .settings import settings


class DatabaseAdapter:
    def __init__(self):
        self.engine = None
        self.session_factory = None
        self.use_supabase = settings.use_supabase
    
    async def initialize(self) -> None:
        """Инициализация подключения к БД."""
        try:
            # Проверяем переменные окружения для определения типа БД
            use_supabase = str(settings.use_supabase).lower() in ('true', '1', 'yes', 'on')
            has_supabase_config = settings.supabase_url and settings.supabase_key
            
            logger.info(f"Настройки БД: use_supabase={use_supabase}, has_config={has_supabase_config}")
            logger.info(f"Supabase URL: {settings.supabase_url}")
            logger.info(f"Supabase Key: {settings.supabase_key[:20] if settings.supabase_key else 'НЕТ'}...")
            
            if use_supabase and has_supabase_config:
                try:
                    logger.info("Попытка инициализации Supabase")
                    await self._init_supabase()
                    logger.info("Supabase инициализирован успешно")
                except Exception as e:
                    logger.error(f"Ошибка Supabase, переключаемся на SQLite: {e}")
                    logger.info("Инициализация SQLite как fallback")
                    await self._init_sqlite()
            else:
                logger.info("Инициализация SQLite")
                await self._init_sqlite()
            
            logger.info("База данных готова к работе")
            
        except Exception as e:
            logger.error("Критическая ошибка инициализации базы данных", error=str(e), exc_info=True)
            raise
    
    async def _init_sqlite(self) -> None:
        """Инициализация SQLite."""
        # Создание движка
        self.engine = create_engine(
            settings.database_url,
            echo=False,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        
        # Создание фабрики сессий
        self.session_factory = sessionmaker(
            self.engine,
            class_=Session,
            expire_on_commit=False,
        )
        
        # Создание таблиц
        Base.metadata.create_all(self.engine)
        logger.info("SQLite инициализирован")
    
    async def _init_supabase(self) -> None:
        """Инициализация Supabase."""
        try:
            # Импортируем Supabase только если нужно
            from supabase import create_client, Client
            
            # Создаем клиент Supabase
            supabase: Client = create_client(settings.supabase_url, settings.supabase_key)
            
            # Проверяем подключение и создаем таблицу если нужно
            try:
                response = supabase.table('tickets').select('*').limit(1).execute()
                logger.info("Таблица tickets существует")
            except Exception as e:
                logger.warning(f"Таблица tickets не найдена или ошибка: {e}")
                logger.info("Попытка создать таблицу tickets...")
                # Создаем таблицу через SQL
                create_table_sql = """
                CREATE TABLE IF NOT EXISTS tickets (
                    id SERIAL PRIMARY KEY,
                    vin VARCHAR(17) NOT NULL,
                    user_id BIGINT NOT NULL,
                    username VARCHAR(255),
                    status VARCHAR(20) NOT NULL DEFAULT 'new',
                    assignee_id BIGINT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                """
                supabase.rpc('exec_sql', {'sql': create_table_sql}).execute()
                logger.info("Таблица tickets создана")
            
            logger.info("Supabase подключен успешно")
            
            # Сохраняем клиент для использования
            self.supabase_client = supabase
            
        except ImportError:
            logger.error("Supabase не установлен. Установите: pip install supabase")
            raise
        except Exception as e:
            logger.error("Ошибка подключения к Supabase", error=str(e))
            raise
    
    async def create_ticket(self, vin: str, user_id: int, username: str = None) -> Dict[str, Any]:
        """Создание заявки."""
        logger.info(f"🎫 Создание заявки: vin={vin}, user_id={user_id}, username={username}, use_supabase={self.use_supabase}")
        
        try:
            if self.use_supabase:
                logger.info("📊 Используем Supabase для создания заявки")
                result = await self._create_ticket_supabase(vin, user_id, username)
            else:
                logger.info("💾 Используем SQLite для создания заявки")
                result = await self._create_ticket_sqlite(vin, user_id, username)
            
            logger.info(f"✅ Заявка создана успешно: {result}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания заявки: {e}", exc_info=True)
            raise
    
    async def _create_ticket_sqlite(self, vin: str, user_id: int, username: str = None) -> Dict[str, Any]:
        """Создание заявки в SQLite."""
        session = self.session_factory()
        try:
            from .models import Ticket
            
            ticket = Ticket(
                vin=vin,
                user_id=user_id,
                status="NEW"
            )
            session.add(ticket)
            session.commit()
            session.refresh(ticket)
            
            return {
                "id": ticket.id,
                "vin": ticket.vin,
                "user_id": ticket.user_id,
                "username": username,
                "status": ticket.status,
                "created_at": ticket.created_at.isoformat()
            }
        finally:
            session.close()
    
    async def _create_ticket_supabase(self, vin: str, user_id: int, username: str = None) -> Dict[str, Any]:
        """Создание заявки в Supabase."""
        from datetime import datetime
        
        ticket_data = {
            "vin": vin,
            "user_id": user_id,
            "status": "NEW",
            "created_at": datetime.now().isoformat()
        }
        
        # Добавляем username только если он не None
        if username:
            ticket_data["username"] = username
        
        logger.debug("Создание заявки в Supabase", ticket_data=ticket_data)
        
        response = self.supabase_client.table('tickets').insert(ticket_data).execute()
        
        logger.debug("Ответ от Supabase", response=response.data)
        
        if response.data:
            return response.data[0]
        else:
            raise Exception("Ошибка создания заявки в Supabase")
    
    async def get_ticket(self, ticket_id: int) -> Optional[Dict[str, Any]]:
        """Получение заявки по ID."""
        if self.use_supabase:
            return await self._get_ticket_supabase(ticket_id)
        else:
            return await self._get_ticket_sqlite(ticket_id)
    
    async def _get_ticket_sqlite(self, ticket_id: int) -> Optional[Dict[str, Any]]:
        """Получение заявки из SQLite."""
        session = self.session_factory()
        try:
            from .models import Ticket
            
            ticket = session.query(Ticket).filter(Ticket.id == ticket_id).first()
            if ticket:
                return {
                    "id": ticket.id,
                    "vin": ticket.vin,
                    "user_id": ticket.user_id,
                    "status": ticket.status,
                    "assignee_id": ticket.assignee_id,
                    "created_at": ticket.created_at.isoformat()
                }
            return None
        finally:
            session.close()
    
    async def _get_ticket_supabase(self, ticket_id: int) -> Optional[Dict[str, Any]]:
        """Получение заявки из Supabase."""
        response = self.supabase_client.table('tickets').select('*').eq('id', ticket_id).execute()
        
        if response.data:
            return response.data[0]
        return None
    
    async def update_ticket_status(self, ticket_id: int, status: str, assignee_id: Optional[int] = None) -> bool:
        """Обновление статуса заявки."""
        if self.use_supabase:
            return await self._update_ticket_supabase(ticket_id, status, assignee_id)
        else:
            return await self._update_ticket_sqlite(ticket_id, status, assignee_id)
    
    async def _update_ticket_sqlite(self, ticket_id: int, status: str, assignee_id: Optional[int] = None) -> bool:
        """Обновление заявки в SQLite."""
        session = self.session_factory()
        try:
            from .models import Ticket
            
            ticket = session.query(Ticket).filter(Ticket.id == ticket_id).first()
            if ticket:
                ticket.status = status
                if assignee_id:
                    ticket.assignee_id = assignee_id
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    async def _update_ticket_supabase(self, ticket_id: int, status: str, assignee_id: Optional[int] = None) -> bool:
        """Обновление заявки в Supabase."""
        try:
            update_data = {"status": status}
            # Временно убираем assignee_id, так как колонка может не существовать
            # if assignee_id:
            #     update_data["assignee_id"] = assignee_id
            
            logger.debug("Обновление заявки в Supabase", ticket_id=ticket_id, update_data=update_data)
            
            response = self.supabase_client.table('tickets').update(update_data).eq('id', ticket_id).execute()
            
            logger.debug("Ответ от Supabase при обновлении", response=response.data)
            
            return len(response.data) > 0
        except Exception as e:
            logger.error("Ошибка обновления заявки в Supabase", ticket_id=ticket_id, error=str(e), exc_info=True)
            raise
    
    async def close(self) -> None:
        """Закрытие подключения."""
        if self.engine:
            self.engine.dispose()
            self.engine = None
            self.session_factory = None


# Глобальный экземпляр адаптера
db_adapter = DatabaseAdapter()