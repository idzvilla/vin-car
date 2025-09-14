"""Обработчики для пользователей."""

from __future__ import annotations

import re
from typing import Optional

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db_session
from ..keyboards import MainKeyboards, TicketKeyboards
from ..models import Ticket
from ..settings import settings
from ..validators import UserInputValidator, VINValidator

# Роутер для пользователей
user_router = Router()


@user_router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot) -> None:
    """Обработчик команды /start.
    
    Args:
        message: Сообщение от пользователя
        bot: Экземпляр бота
    """
    user_id = message.from_user.id
    username = message.from_user.username or "пользователь"
    
    logger.info("Пользователь запустил бота", user_id=user_id, username=username)
    
    welcome_text = (
        "🚗 <b>Добро пожаловать в VIN Report Bot!</b>\n\n"
        "Я помогу вам получить отчет по VIN номеру вашего автомобиля.\n\n"
        "📋 <b>Как это работает:</b>\n"
        "1. Отправьте мне VIN номер (17 символов)\n"
        "2. Я создам заявку и передам её менеджеру\n"
        "3. Менеджер обработает заявку и отправит вам PDF отчет\n\n"
        "💡 <b>Пример VIN:</b> 1HGBH41JXMN109186\n\n"
        "Просто отправьте VIN номер в следующем сообщении!"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=MainKeyboards.get_start_keyboard(),
        parse_mode="HTML"
    )


@user_router.message(Command("help"))
async def cmd_help(message: Message, bot: Bot) -> None:
    """Обработчик команды /help.
    
    Args:
        message: Сообщение от пользователя
        bot: Экземпляр бота
    """
    user_id = message.from_user.id
    
    logger.info("Пользователь запросил помощь", user_id=user_id)
    
    help_text = (
        "📖 <b>Справка по использованию бота</b>\n\n"
        "🔍 <b>Что такое VIN?</b>\n"
        "VIN (Vehicle Identification Number) — это уникальный 17-символьный "
        "идентификатор автомобиля.\n\n"
        "📝 <b>Как получить отчет:</b>\n"
        "1. Найдите VIN номер на автомобиле (обычно на лобовом стекле, "
        "дверной табличке или в документах)\n"
        "2. Отправьте VIN боту (17 символов без пробелов)\n"
        "3. Дождитесь обработки заявки менеджером\n"
        "4. Получите PDF отчет в личные сообщения\n\n"
        "⚠️ <b>Важно:</b>\n"
        "• VIN должен содержать ровно 17 символов\n"
        "• Не используйте буквы I, O, Q\n"
        "• Время обработки: 5-30 минут\n\n"
        "❓ <b>Проблемы?</b>\n"
        "Если у вас возникли вопросы, обратитесь в поддержку."
    )
    
    await message.answer(
        help_text,
        reply_markup=MainKeyboards.get_help_keyboard(),
        parse_mode="HTML"
    )


@user_router.message(F.text)
async def handle_vin_message(message: Message, bot: Bot) -> None:
    """Обработчик текстовых сообщений с VIN номерами.
    
    Args:
        message: Сообщение от пользователя
        bot: Экземпляр бота
    """
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    text = message.text.strip()
    
    logger.info("Получено текстовое сообщение", user_id=user_id, text_length=len(text))
    
    # Валидация VIN
    is_valid, error_message = VINValidator.validate(text)
    if not is_valid:
        await message.answer(
            f"❌ <b>Ошибка валидации VIN</b>\n\n{error_message}\n\n"
            "💡 <b>Правильный формат:</b> 17 символов без I, O, Q\n"
            "📝 <b>Пример:</b> 1HGBH41JXMN109186",
            parse_mode="HTML"
        )
        return
    
    # Нормализация VIN
    normalized_vin = VINValidator.normalize(text)
    
    try:
        # Создание заявки
        async with get_db_session() as session:
            # Проверка на дублирование
            existing_ticket = await session.execute(
                select(Ticket).where(
                    Ticket.vin == normalized_vin,
                    Ticket.user_id == user_id,
                    Ticket.status.in_(["NEW", "TAKEN"])
                )
            )
            existing_ticket = existing_ticket.scalar_one_or_none()
            
            if existing_ticket:
                await message.answer(
                    f"⚠️ <b>Заявка уже существует</b>\n\n"
                    f"Заявка №{existing_ticket.id} с VIN <code>{normalized_vin}</code> "
                    f"уже обрабатывается.\n\n"
                    f"📊 <b>Статус:</b> {_get_status_text(existing_ticket.status)}",
                    parse_mode="HTML"
                )
                return
            
            # Создание новой заявки
            ticket = Ticket(
                vin=normalized_vin,
                user_id=user_id,
                status="NEW"
            )
            session.add(ticket)
            await session.commit()
            await session.refresh(ticket)
            
            logger.info(
                "Создана новая заявка",
                ticket_id=ticket.id,
                user_id=user_id,
                vin=normalized_vin
            )
            
            # Уведомление пользователя
            await message.answer(
                f"✅ <b>Заявка принята!</b>\n\n"
                f"🆔 <b>Номер заявки:</b> #{ticket.id}\n"
                f"🚗 <b>VIN:</b> <code>{normalized_vin}</code>\n"
                f"📊 <b>Статус:</b> в работе\n\n"
                f"⏰ <b>Время обработки:</b> 5-30 минут\n"
                f"📄 <b>Отчет будет отправлен</b> в личные сообщения",
                parse_mode="HTML"
            )
            
            # Отправка карточки заявки в чат менеджеров
            await _send_ticket_to_managers(bot, ticket, username)
            
    except Exception as e:
        logger.error("Ошибка создания заявки", user_id=user_id, error=str(e))
        await message.answer(
            "❌ <b>Произошла ошибка</b>\n\n"
            "Не удалось создать заявку. Попробуйте позже или обратитесь в поддержку.",
            parse_mode="HTML"
        )


async def _send_ticket_to_managers(bot: Bot, ticket: Ticket, username: str) -> None:
    """Отправка карточки заявки в чат менеджеров.
    
    Args:
        bot: Экземпляр бота
        ticket: Заявка
        username: Имя пользователя
    """
    try:
        ticket_text = (
            f"🆕 <b>Новая заявка №{ticket.id}</b>\n\n"
            f"👤 <b>От:</b> @{username} (ID: {ticket.user_id})\n"
            f"🚗 <b>VIN:</b> <code>{ticket.vin}</code>\n"
            f"📅 <b>Создана:</b> {ticket.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"📊 <b>Статус:</b> новая"
        )
        
        await bot.send_message(
            chat_id=settings.manager_chat_id,
            text=ticket_text,
            reply_markup=TicketKeyboards.get_take_keyboard(ticket.id),
            parse_mode="HTML"
        )
        
        logger.info(
            "Заявка отправлена менеджерам",
            ticket_id=ticket.id,
            manager_chat_id=settings.manager_chat_id
        )
        
    except Exception as e:
        logger.error(
            "Ошибка отправки заявки менеджерам",
            ticket_id=ticket.id,
            error=str(e)
        )


def _get_status_text(status: str) -> str:
    """Получение текстового представления статуса.
    
    Args:
        status: Статус заявки
        
    Returns:
        Текстовое представление статуса
    """
    status_map = {
        "NEW": "новая",
        "TAKEN": "в работе",
        "DONE": "завершена"
    }
    return status_map.get(status, "неизвестно")
