#!/usr/bin/env python3
"""Тест нового бота без polling."""

import asyncio
from aiogram import Bot
from src.settings import settings

async def test_bot():
    """Простой тест бота."""
    bot = Bot(token=settings.bot_token)
    
    try:
        # Получение информации о боте
        bot_info = await bot.get_me()
        print(f"✅ Бот найден: @{bot_info.username} (ID: {bot_info.id})")
        
        # Отправка тестового сообщения в чат менеджеров
        test_message = (
            "🧪 <b>Тест нового бота</b>\n\n"
            "Если вы видите это сообщение, значит бот работает!"
        )
        
        await bot.send_message(
            chat_id=settings.manager_chat_id,
            text=test_message,
            parse_mode="HTML"
        )
        
        print("✅ Тестовое сообщение отправлено!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(test_bot())





