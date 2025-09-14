#!/usr/bin/env python3
"""Тест подключения к Supabase."""

import asyncio
from src.supabase_db import init_supabase, supabase_manager

async def test_supabase():
    """Тест подключения к Supabase."""
    try:
        print("🔄 Тестирование подключения к Supabase...")
        
        # Инициализация
        await init_supabase()
        print("✅ Supabase инициализирован")
        
        # Тест создания заявки
        print("🔄 Тестирование создания заявки...")
        ticket = await supabase_manager.create_ticket(
            user_id=123456789,
            username="test_user",
            vin="1HGBH41JXMN109186"
        )
        print(f"✅ Заявка создана: {ticket}")
        
        # Тест получения заявки
        print("🔄 Тестирование получения заявки...")
        retrieved_ticket = await supabase_manager.get_ticket(ticket["id"])
        print(f"✅ Заявка получена: {retrieved_ticket}")
        
        # Тест обновления статуса
        print("🔄 Тестирование обновления статуса...")
        success = await supabase_manager.update_ticket_status(
            ticket["id"], 
            "DONE", 
            assignee_id=987654321
        )
        print(f"✅ Статус обновлен: {success}")
        
        print("🎉 Все тесты прошли успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_supabase())





