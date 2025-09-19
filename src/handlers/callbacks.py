"""Обработчики callback запросов."""

from __future__ import annotations

import asyncio
import re
from typing import Optional

from aiogram import Bot, Router
from aiogram.types import CallbackQuery
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db_session
from ..keyboards import PaymentKeyboards, TicketKeyboards
from ..models import Ticket
from ..settings import settings
from .user import _handle_payment_cancellation, _handle_payment_confirmation, _handle_payment_selection

# Роутер для callback'ов
callback_router = Router()


@callback_router.callback_query(lambda c: c.data.startswith("take_ticket:"))
async def handle_take_ticket(callback: CallbackQuery, bot: Bot) -> None:
    """Обработчик назначения заявки.
    
    Args:
        callback: Callback запрос
        bot: Экземпляр бота
    """
    # Проверка, что callback в чате менеджеров
    if callback.message and callback.message.chat.id != settings.manager_chat_id:
        await callback.answer("❌ Эта функция доступна только в чате менеджеров.")
        return
    
    # Извлечение ID заявки
    ticket_id_match = re.search(r"take_ticket:(\d+)", callback.data)
    if not ticket_id_match:
        await callback.answer("❌ Ошибка: неверный формат запроса.")
        return
    
    try:
        ticket_id = int(ticket_id_match.group(1))
    except ValueError:
        await callback.answer("❌ Ошибка: неверный номер заявки.")
        return
    
    manager_id = callback.from_user.id
    manager_username = callback.from_user.username or f"manager_{manager_id}"
    
    try:
        from src.db_adapter import db_adapter
        
        # Получение заявки с повторными попытками
        ticket_data = None
        for attempt in range(3):
            ticket_data = await db_adapter.get_ticket(ticket_id)
            if ticket_data:
                break
            await asyncio.sleep(0.2)  # Небольшая задержка между попытками
        
        if not ticket_data:
            await callback.answer("❌ Заявка не найдена. Попробуйте через несколько секунд.")
            return
        
        # Проверка статуса заявки
        if ticket_data['status'] != 'NEW':
            await callback.answer("❌ Заявка уже назначена или завершена.")
            return
        
        # Назначение заявки
        await db_adapter.update_ticket_status(ticket_id, "TAKEN", manager_id)
        
        logger.info(
            "Заявка назначена менеджеру",
            ticket_id=ticket_id,
            manager_id=manager_id,
            manager_username=manager_username
        )
        
        # Обновление сообщения
        if callback.message:
            from datetime import datetime
            created_at = datetime.fromisoformat(ticket_data['created_at'].replace('Z', '+00:00'))
            
            updated_text = (
                f"🆕 <b>Новая заявка №{ticket_data['id']}</b>\n\n"
                f"👤 <b>От:</b> @{manager_username} (ID: {ticket_data['user_id']})\n"
                f"🚗 <b>VIN:</b> <code>{ticket_data['vin']}</code>\n"
                f"📅 <b>Создана:</b> {created_at.strftime('%d.%m.%Y %H:%M')}\n"
                f"📊 <b>Статус:</b> назначена\n"
                f"👨‍💼 <b>Назначена:</b> @{manager_username}"
            )
            
            await callback.message.edit_text(
                text=updated_text,
                reply_markup=TicketKeyboards.get_taken_keyboard(ticket_id),
                parse_mode="HTML"
            )
        
        await callback.answer("✅ Заявка назначена вам!")
            
    except Exception as e:
        logger.error(
            "Ошибка назначения заявки",
            ticket_id=ticket_id,
            manager_id=manager_id,
            error=str(e)
        )
        await callback.answer("❌ Произошла ошибка при назначении заявки.")


@callback_router.callback_query(lambda c: c.data.startswith("done_hint:"))
async def handle_done_hint(callback: CallbackQuery, bot: Bot) -> None:
    """Обработчик подсказки о завершении заявки.
    
    Args:
        callback: Callback запрос
        bot: Экземпляр бота
    """
    # Проверка, что callback в чате менеджеров
    if callback.message and callback.message.chat.id != settings.manager_chat_id:
        await callback.answer("❌ Эта функция доступна только в чате менеджеров.")
        return
    
    # Извлечение ID заявки
    ticket_id_match = re.search(r"done_hint:(\d+)", callback.data)
    if not ticket_id_match:
        await callback.answer("❌ Ошибка: неверный формат запроса.")
        return
    
    try:
        ticket_id = int(ticket_id_match.group(1))
    except ValueError:
        await callback.answer("❌ Ошибка: неверный номер заявки.")
        return
    
    hint_text = (
        "📋 <b>Как завершить заявку:</b>\n\n"
        "1️⃣ <b>Отправьте PDF в ответ</b> на карточку заявки\n"
        "2️⃣ <b>Или используйте команду:</b> /done {ticket_id} + PDF\n\n"
        "💡 <b>Важно:</b>\n"
        "• Файл должен быть в формате PDF\n"
        "• Максимальный размер: 50 МБ\n"
        "• Отчет будет автоматически отправлен пользователю"
    ).format(ticket_id=ticket_id)
    
    await callback.message.answer(
        hint_text,
        reply_markup=TicketKeyboards.get_done_hint_keyboard(ticket_id),
        parse_mode="HTML"
    )
    
    await callback.answer("💡 Инструкция отправлена!")


@callback_router.callback_query(lambda c: c.data.startswith("send_pdf_hint:"))
async def handle_send_pdf_hint(callback: CallbackQuery, bot: Bot) -> None:
    """Обработчик подсказки об отправке PDF.
    
    Args:
        callback: Callback запрос
        bot: Экземпляр бота
    """
    await callback.answer("📤 Отправьте PDF в ответ на карточку заявки!")


@callback_router.callback_query(lambda c: c.data.startswith("command_hint:"))
async def handle_command_hint(callback: CallbackQuery, bot: Bot) -> None:
    """Обработчик подсказки о команде.
    
    Args:
        callback: Callback запрос
        bot: Экземпляр бота
    """
    # Извлечение ID заявки
    ticket_id_match = re.search(r"command_hint:(\d+)", callback.data)
    if not ticket_id_match:
        await callback.answer("❌ Ошибка: неверный формат запроса.")
        return
    
    try:
        ticket_id = int(ticket_id_match.group(1))
    except ValueError:
        await callback.answer("❌ Ошибка: неверный номер заявки.")
        return
    
    command_text = f"/done {ticket_id}"
    
    await callback.answer(f"💬 Команда: {command_text}")


@callback_router.callback_query(lambda c: c.data == "help_info")
async def handle_help_info(callback: CallbackQuery, bot: Bot) -> None:
    """Обработчик информации о помощи.
    
    Args:
        callback: Callback запрос
        bot: Экземпляр бота
    """
    help_text = (
        "📖 <b>Как получить VIN отчет:</b>\n\n"
        "1️⃣ <b>Найдите VIN номер</b> на автомобиле:\n"
        "• Лобовое стекло (слева внизу)\n"
        "• Дверная табличка\n"
        "• В документах на автомобиль\n\n"
        "2️⃣ <b>Отправьте VIN боту</b> (17 символов)\n\n"
        "3️⃣ <b>Дождитесь обработки</b> (5-30 минут)\n\n"
        "4️⃣ <b>Получите PDF отчет</b> в личные сообщения\n\n"
        "💡 <b>Пример VIN:</b> 1HGBH41JXMN109186"
    )
    
    await callback.message.edit_text(
        help_text,
        reply_markup=MainKeyboards.get_help_keyboard(),
        parse_mode="HTML"
    )
    
    await callback.answer()


@callback_router.callback_query(lambda c: c.data == "support_info")
async def handle_support_info(callback: CallbackQuery, bot: Bot) -> None:
    """Обработчик информации о поддержке.
    
    Args:
        callback: Callback запрос
        bot: Экземпляр бота
    """
    support_text = (
        "📞 <b>Поддержка</b>\n\n"
        "Если у вас возникли вопросы или проблемы:\n\n"
        "💬 <b>Напишите в поддержку:</b> @support_username\n"
        "📧 <b>Email:</b> support@example.com\n"
        "🕒 <b>Время работы:</b> 9:00 - 18:00 МСК\n\n"
        "📋 <b>При обращении укажите:</b>\n"
        "• Номер заявки (если есть)\n"
        "• VIN номер автомобиля\n"
        "• Описание проблемы"
    )
    
    await callback.message.edit_text(
        support_text,
        reply_markup=MainKeyboards.get_help_keyboard(),
        parse_mode="HTML"
    )
    
    await callback.answer()


@callback_router.callback_query(lambda c: c.data == "back_to_start")
async def handle_back_to_start(callback: CallbackQuery, bot: Bot) -> None:
    """Обработчик возврата к началу.
    
    Args:
        callback: Callback запрос
        bot: Экземпляр бота
    """
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
    
    await callback.message.edit_text(
        welcome_text,
        reply_markup=MainKeyboards.get_start_keyboard(),
        parse_mode="HTML"
    )
    
    await callback.answer()


# Обработчики платежей
@callback_router.callback_query(lambda c: c.data.startswith("payment:"))
async def handle_payment_selection(callback: CallbackQuery) -> None:
    """Обработчик выбора тарифа оплаты."""
    payment_type = callback.data.split(":", 1)[1]
    await _handle_payment_selection(callback, payment_type)
    await callback.answer()


@callback_router.callback_query(lambda c: c.data.startswith("confirm_payment:"))
async def handle_payment_confirmation(callback: CallbackQuery) -> None:
    """Обработчик подтверждения платежа."""
    try:
        payment_id = int(callback.data.split(":", 1)[1])
        await _handle_payment_confirmation(callback, payment_id)
    except ValueError:
        await callback.answer("❌ Ошибка: неверный ID платежа.")
    await callback.answer()


@callback_router.callback_query(lambda c: c.data.startswith("cancel_payment:"))
async def handle_payment_cancellation(callback: CallbackQuery) -> None:
    """Обработчик отмены платежа."""
    try:
        payment_id = int(callback.data.split(":", 1)[1])
        await _handle_payment_cancellation(callback, payment_id)
    except ValueError:
        await callback.answer("❌ Ошибка: неверный ID платежа.")
    await callback.answer()


@callback_router.callback_query(lambda c: c.data == "check_payment_status")
async def handle_check_payment_status(callback: CallbackQuery) -> None:
    """Обработчик проверки статуса платежа."""
    user_id = callback.from_user.id
    
    from ..payment_service import PaymentService
    
    subscription = await PaymentService.get_user_subscription(user_id)
    
    if subscription:
        status_text = (
            f"📊 <b>Статус вашей подписки</b>\n\n"
            f"📈 <b>Всего куплено отчетов:</b> {subscription.total_reports}\n"
            f"📊 <b>Осталось отчетов:</b> {subscription.reports_remaining}\n"
            f"📅 <b>Подписка создана:</b> {subscription.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"✅ Подписка активна! Можете отправлять VIN номера."
        )
    else:
        status_text = (
            "❌ <b>У вас нет активной подписки</b>\n\n"
            "Для получения отчетов необходимо произвести оплату.\n"
            "Выберите тариф и оплатите подписку."
        )
    
    await callback.message.edit_text(
        status_text,
        reply_markup=PaymentKeyboards.get_payment_status_keyboard(),
        parse_mode="HTML"
    )
    
    await callback.answer()


@callback_router.callback_query(lambda c: c.data == "back_to_payment")
async def handle_back_to_payment(callback: CallbackQuery) -> None:
    """Обработчик возврата к выбору тарифа."""
    payment_text = (
        "💳 <b>Выберите тариф для оплаты</b>\n\n"
        "💳 <b>1 отчет - $2.00</b>\n"
        "📦 <b>100 отчетов - $100.00</b> (экономия $100!)\n\n"
        "Выберите тариф:"
    )
    
    await callback.message.edit_text(
        payment_text,
        reply_markup=PaymentKeyboards.get_payment_options_keyboard(),
        parse_mode="HTML"
    )
    
    await callback.answer()
