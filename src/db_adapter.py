"""Адаптер базы данных для работы с SQLite и Supabase."""

from __future__ import annotations

import asyncio
from typing import Optional, Dict, Any
from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from .models import Base
from .settings import settings


class DatabaseAdapter:
    """Адаптер для работы с различными базами данных."""
    
    def __init__(self):
        """Инициализация адаптера."""
        self.engine = None
        self.session_factory = None
        self.use_supabase = settings.use_supabase
    
    async def initialize(self) -> None:
        """Инициализация подключения к БД."""
        try:
            if self.use_supabase and settings.supabase_url and settings.supabase_key:
                logger.info("Инициализация Supabase")
                await self._init_supabase()
            else:
                logger.info("Инициализация SQLite")
                await self._init_sqlite()
            
            logger.info("База данных готова к работе")
            
        except Exception as e:
            logger.error("Ошибка инициализации базы данных", error=str(e), exc_info=True)
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
            
            # Проверяем подключение
            response = supabase.table('tickets').select('*').limit(1).execute()
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
        if self.use_supabase:
            return await self._create_ticket_supabase(vin, user_id, username)
        else:
            return await self._create_ticket_sqlite(vin, user_id, username)
    
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