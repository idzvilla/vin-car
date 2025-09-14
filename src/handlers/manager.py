"""Обработчики для менеджеров."""

from __future__ import annotations

import re
from typing import Optional

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import Document, Message
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db_session
from ..keyboards import TicketKeyboards
from ..models import Ticket
from ..settings import settings
from ..validators import MessageValidator

# Роутер для менеджеров
manager_router = Router()


@manager_router.message(Command("done"))
async def cmd_done(message: Message, bot: Bot) -> None:
    """Обработчик команды /done для завершения заявки.
    
    Args:
        message: Сообщение от менеджера
        bot: Экземпляр бота
    """
    # Проверка, что команда вызвана в чате менеджеров
    if message.chat.id != settings.manager_chat_id:
        await message.answer("❌ Эта команда доступна только в чате менеджеров.")
        return
    
    # Проверка наличия документа
    if not message.document:
        await message.answer(
            "❌ <b>Ошибка</b>\n\n"
            "Для завершения заявки необходимо прикрепить PDF документ.\n\n"
            "💡 <b>Использование:</b> /done &lt;номер_заявки&gt; + PDF",
            parse_mode="HTML"
        )
        return
    
    # Извлечение номера заявки из команды
    command_text = message.text or ""
    ticket_id_match = re.search(r"/done\s+(\d+)", command_text)
    
    if not ticket_id_match:
        await message.answer(
            "❌ <b>Ошибка</b>\n\n"
            "Не указан номер заявки.\n\n"
            "💡 <b>Использование:</b> /done 123 + PDF",
            parse_mode="HTML"
        )
        return
    
    try:
        ticket_id = int(ticket_id_match.group(1))
    except ValueError:
        await message.answer(
            "❌ <b>Ошибка</b>\n\n"
            "Неверный формат номера заявки.\n\n"
            "💡 <b>Использование:</b> /done 123 + PDF",
            parse_mode="HTML"
        )
        return
    
    # Валидация документа
    document = message.document
    is_valid_size, size_error = MessageValidator.validate_document_size(
        document.file_size,
        settings.max_file_size
    )
    
    if not is_valid_size:
        await message.answer(f"❌ <b>Ошибка размера файла</b>\n\n{size_error}", parse_mode="HTML")
        return
    
    # Проверка типа файла
    if not document.file_name or not document.file_name.lower().endswith('.pdf'):
        await message.answer(
            "❌ <b>Ошибка типа файла</b>\n\n"
            "Пожалуйста, отправьте PDF документ.",
            parse_mode="HTML"
        )
        return
    
    # Обработка заявки
    await _process_ticket_completion(bot, message, ticket_id, document)


@manager_router.message(F.document)
async def handle_document_reply(message: Message, bot: Bot) -> None:
    """Обработчик документов в ответ на карточку заявки.
    
    Args:
        message: Сообщение с документом
        bot: Экземпляр бота
    """
    # Проверка, что сообщение в чате менеджеров
    if message.chat.id != settings.manager_chat_id:
        return
    
    # Проверка, что это ответ на сообщение
    if not message.reply_to_message:
        return
    
    # Извлечение номера заявки из текста сообщения, на которое отвечают
    replied_text = message.reply_to_message.text or ""
    ticket_id_match = re.search(r"заявка №(\d+)", replied_text, re.IGNORECASE)
    
    if not ticket_id_match:
        return
    
    try:
        ticket_id = int(ticket_id_match.group(1))
    except ValueError:
        logger.warning("Неверный формат номера заявки в ответе", text=replied_text)
        return
    
    # Валидация документа
    document = message.document
    is_valid_size, size_error = MessageValidator.validate_document_size(
        document.file_size,
        settings.max_file_size
    )
    
    if not is_valid_size:
        await message.answer(f"❌ <b>Ошибка размера файла</b>\n\n{size_error}", parse_mode="HTML")
        return
    
    # Проверка типа файла
    if not document.file_name or not document.file_name.lower().endswith('.pdf'):
        await message.answer(
            "❌ <b>Ошибка типа файла</b>\n\n"
            "Пожалуйста, отправьте PDF документ.",
            parse_mode="HTML"
        )
        return
    
    # Обработка заявки
    await _process_ticket_completion(bot, message, ticket_id, document)


async def _process_ticket_completion(
    bot: Bot,
    message: Message,
    ticket_id: int,
    document: Document
) -> None:
    """Обработка завершения заявки.
    
    Args:
        bot: Экземпляр бота
        message: Сообщение от менеджера
        ticket_id: ID заявки
        document: PDF документ
    """
    manager_id = message.from_user.id
    manager_username = message.from_user.username or f"manager_{manager_id}"
    
    try:
        async with get_db_session() as session:
            # Поиск заявки
            result = await session.execute(
                select(Ticket).where(Ticket.id == ticket_id)
            )
            ticket = result.scalar_one_or_none()
            
            if not ticket:
                await message.answer(
                    f"❌ <b>Заявка не найдена</b>\n\n"
                    f"Заявка №{ticket_id} не существует.",
                    parse_mode="HTML"
                )
                return
            
            # Проверка статуса заявки
            if ticket.status == "DONE":
                await message.answer(
                    f"⚠️ <b>Заявка уже завершена</b>\n\n"
                    f"Заявка №{ticket_id} уже была закрыта.",
                    parse_mode="HTML"
                )
                return
            
            # Обновление статуса заявки
            ticket.status = "DONE"
            ticket.assignee_id = manager_id
            await session.commit()
            
            logger.info(
                "Заявка завершена менеджером",
                ticket_id=ticket_id,
                manager_id=manager_id,
                manager_username=manager_username
            )
            
            # Отправка отчета пользователю
            await _send_report_to_user(bot, ticket, document)
            
            # Подтверждение менеджеру
            await message.answer(
                f"✅ <b>Отчет отправлен!</b>\n\n"
                f"📄 Заявка №{ticket_id} закрыта\n"
                f"👤 Отчет отправлен пользователю",
                parse_mode="HTML"
            )
            
            # Обновление карточки заявки (удаление кнопок)
            if message.reply_to_message:
                try:
                    await message.reply_to_message.edit_reply_markup(
                        reply_markup=TicketKeyboards.get_empty_keyboard()
                    )
                except Exception as e:
                    logger.warning("Не удалось обновить карточку заявки", error=str(e))
            
    except Exception as e:
        logger.error(
            "Ошибка завершения заявки",
            ticket_id=ticket_id,
            manager_id=manager_id,
            error=str(e)
        )
        await message.answer(
            "❌ <b>Произошла ошибка</b>\n\n"
            "Не удалось завершить заявку. Попробуйте позже.",
            parse_mode="HTML"
        )


async def _send_report_to_user(bot: Bot, ticket: Ticket, document: Document) -> None:
    """Отправка отчета пользователю.
    
    Args:
        bot: Экземпляр бота
        ticket: Заявка
        document: PDF документ
    """
    try:
        # Уведомление о готовности отчета
        await bot.send_message(
            chat_id=ticket.user_id,
            text=f"✅ <b>Заявка №{ticket.id}: отчет готов!</b>\n\n"
                 f"🚗 <b>VIN:</b> <code>{ticket.vin}</code>\n"
                 f"📄 <b>Ваш отчет (PDF)</b> прикреплен к сообщению ниже.",
            parse_mode="HTML"
        )
        
        # Пересылка документа пользователю
        await bot.send_document(
            chat_id=ticket.user_id,
            document=document.file_id,
            caption="📄 Ваш отчет (PDF)",
            parse_mode="HTML"
        )
        
        logger.info(
            "Отчет отправлен пользователю",
            ticket_id=ticket.id,
            user_id=ticket.user_id
        )
        
    except Exception as e:
        logger.error(
            "Ошибка отправки отчета пользователю",
            ticket_id=ticket.id,
            user_id=ticket.user_id,
            error=str(e)
        )





