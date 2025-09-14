"""Работа с базой данных через Supabase."""

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
from loguru import logger

try:
    from supabase import create_client, Client
    from src.supabase_config import supabase_settings
    SUPABASE_AVAILABLE = True
except ImportError as e:
    SUPABASE_AVAILABLE = False
    logger.warning(f"Supabase не установлен: {e}. Установите: pip install supabase")


class SupabaseManager:
    """Менеджер для работы с Supabase."""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.initialized = False
    
    def initialize(self) -> None:
        """Инициализация Supabase клиента."""
        if not SUPABASE_AVAILABLE:
            raise RuntimeError("Supabase не установлен")
        
        if not supabase_settings.supabase_url or not supabase_settings.supabase_key:
            raise RuntimeError("Не настроены SUPABASE_URL и SUPABASE_KEY")
        
        try:
            self.client = create_client(
                supabase_settings.supabase_url,
                supabase_settings.supabase_key
            )
            self.initialized = True
            logger.info("Supabase клиент инициализирован")
        except Exception as e:
            logger.error(f"Ошибка инициализации Supabase: {e}")
            raise
    
    async def create_ticket(self, user_id: int, username: str, vin: str) -> Dict[str, Any]:
        """Создание новой заявки."""
        if not self.initialized:
            raise RuntimeError("Supabase не инициализирован")
        
        try:
            ticket_data = {
                "user_id": user_id,
                "username": username,
                "vin": vin,
                "status": "NEW",
                "created_at": datetime.now().isoformat()
            }
            
            result = self.client.table("tickets").insert(ticket_data).execute()
            
            if result.data:
                ticket = result.data[0]
                logger.info(f"Заявка создана в Supabase: {ticket['id']}")
                return ticket
            else:
                raise RuntimeError("Не удалось создать заявку")
                
        except Exception as e:
            logger.error(f"Ошибка создания заявки в Supabase: {e}")
            raise
    
    async def get_ticket(self, ticket_id: int) -> Optional[Dict[str, Any]]:
        """Получение заявки по ID."""
        if not self.initialized:
            raise RuntimeError("Supabase не инициализирован")
        
        try:
            result = self.client.table("tickets").select("*").eq("id", ticket_id).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения заявки из Supabase: {e}")
            return None
    
    async def update_ticket_status(self, ticket_id: int, status: str, assignee_id: Optional[int] = None) -> bool:
        """Обновление статуса заявки."""
        if not self.initialized:
            raise RuntimeError("Supabase не инициализирован")
        
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.now().isoformat()
            }
            
            if assignee_id:
                update_data["assignee_id"] = assignee_id
            
            result = self.client.table("tickets").update(update_data).eq("id", ticket_id).execute()
            
            if result.data:
                logger.info(f"Статус заявки {ticket_id} обновлен на {status}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Ошибка обновления заявки в Supabase: {e}")
            return False
    
    async def get_tickets_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Получение заявок по статусу."""
        if not self.initialized:
            raise RuntimeError("Supabase не инициализирован")
        
        try:
            result = self.client.table("tickets").select("*").eq("status", status).order("created_at", desc=True).execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Ошибка получения заявок из Supabase: {e}")
            return []
    
    async def get_user_tickets(self, user_id: int) -> List[Dict[str, Any]]:
        """Получение заявок пользователя."""
        if not self.initialized:
            raise RuntimeError("Supabase не инициализирован")
        
        try:
            result = self.client.table("tickets").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Ошибка получения заявок пользователя из Supabase: {e}")
            return []


# Глобальный менеджер Supabase
supabase_manager = SupabaseManager()


async def init_supabase() -> None:
    """Инициализация Supabase."""
    try:
        supabase_manager.initialize()
        logger.info("Supabase готов к работе")
    except Exception as e:
        logger.error(f"Ошибка инициализации Supabase: {e}")
        raise


def close_supabase() -> None:
    """Закрытие Supabase соединения."""
    supabase_manager.initialized = False
    logger.info("Supabase соединение закрыто")
