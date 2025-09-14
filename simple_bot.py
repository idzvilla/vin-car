#!/usr/bin/env python3
"""Простая версия VIN Report Bot для тестирования."""

import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message
from aiogram.filters import Command
from loguru import logger

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logger.remove()
logger.add("logs/bot.log", level="INFO", rotation="1 day")

# Создаем бота
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()
router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start."""
    await message.answer(
        "🚗 <b>Добро пожаловать в VIN Report Bot!</b>\n\n"
        "Отправьте мне VIN номер (17 символов) для получения отчета.\n\n"
        "💡 <b>Пример:</b> 1HGBH41JXMN109186",
        parse_mode="HTML"
    )

@router.message(F.text)
async def handle_vin(message: Message):
    """Обработчик VIN номеров."""
    vin = message.text.strip().upper()
    
    # Простая валидация VIN
    if len(vin) != 17:
        await message.answer("❌ VIN должен содержать ровно 17 символов")
        return
    
    if not vin.isalnum() or 'I' in vin or 'O' in vin or 'Q' in vin:
        await message.answer("❌ VIN содержит недопустимые символы")
        return
    
    # Отправляем уведомление менеджерам
    manager_chat_id = os.getenv("MANAGER_CHAT_ID")
    if manager_chat_id:
        try:
            await bot.send_message(
                chat_id=int(manager_chat_id),
                text=f"🆕 <b>Новая заявка</b>\n\n"
                     f"👤 <b>От:</b> @{message.from_user.username or message.from_user.id}\n"
                     f"🚗 <b>VIN:</b> <code>{vin}</code>",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Ошибка отправки в чат менеджеров: {e}")
    
    await message.answer(
        f"✅ <b>Заявка принята!</b>\n\n"
        f"🚗 <b>VIN:</b> <code>{vin}</code>\n"
        f"📊 <b>Статус:</b> в работе\n\n"
        f"⏰ <b>Время обработки:</b> 5-30 минут",
        parse_mode="HTML"
    )

async def main():
    """Главная функция."""
    try:
        logger.info("Запуск VIN Report Bot")
        
        # Получаем информацию о боте
        bot_info = await bot.get_me()
        logger.info(f"Бот запущен: @{bot_info.username}")
        
        # Регистрируем роутер
        dp.include_router(router)
        
        # Запускаем polling
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    # Создаем директории
    os.makedirs("logs", exist_ok=True)
    
    # Запускаем бота
    asyncio.run(main())





