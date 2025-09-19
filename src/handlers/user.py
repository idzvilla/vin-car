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
from ..keyboards import MainKeyboards, PaymentKeyboards, TicketKeyboards
from ..models import Ticket
from ..payment_service import PaymentService
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
    
    # Проверяем подписку пользователя
    subscription = await PaymentService.get_user_subscription(user_id)
    
    if subscription and subscription.can_generate_report():
        subscription_info = (
            f"📊 <b>Ваша подписка:</b> {subscription.reports_remaining} отчетов\n"
            f"📈 <b>Всего куплено:</b> {subscription.total_reports}\n\n"
        )
    else:
        subscription_info = (
            "💳 <b>Для получения отчетов необходима оплата:</b>\n"
            "• 1 отчет - $2.00\n"
            "• 100 отчетов - $100.00 (экономия $100!)\n\n"
        )
    
    welcome_text = (
        "🚗 <b>Добро пожаловать в VIN Report Bot!</b>\n\n"
        "Я помогу вам получить отчет по VIN номеру вашего автомобиля.\n\n"
        f"{subscription_info}"
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


@user_router.message(F.document)
async def handle_document_reply(message: Message, bot: Bot) -> None:
    """Обработчик документов в ответ на карточку заявки."""
    # Проверка, что сообщение в чате менеджеров
    if message.chat.id != settings.manager_chat_id:
        return
    
    # Проверка, что это ответ на сообщение
    if not message.reply_to_message:
        await message.answer(
            "❌ <b>Ошибка</b>\n\n"
            "Для завершения заявки отправьте PDF <b>в ответ</b> на карточку заявки.",
            parse_mode="HTML"
        )
        return
    
    # Извлечение номера заявки из текста сообщения, на которое отвечают
    replied_text = message.reply_to_message.text or ""
    ticket_id_match = re.search(r"заявка №(\d+)", replied_text, re.IGNORECASE)
    
    if not ticket_id_match:
        await message.answer(
            "❌ <b>Ошибка</b>\n\n"
            "Не удалось найти номер заявки в сообщении.",
            parse_mode="HTML"
        )
        return
    
    try:
        ticket_id = int(ticket_id_match.group(1))
    except ValueError:
        await message.answer(
            "❌ <b>Ошибка</b>\n\n"
            "Неверный формат номера заявки.",
            parse_mode="HTML"
        )
        return
    
    # Проверка типа файла
    if not message.document.file_name or not message.document.file_name.lower().endswith('.pdf'):
        await message.answer(
            "❌ <b>Ошибка типа файла</b>\n\n"
            "Пожалуйста, отправьте PDF документ.",
            parse_mode="HTML"
        )
        return
    
    # Проверка размера файла (50 МБ)
    if message.document.file_size > 50 * 1024 * 1024:
        await message.answer(
            "❌ <b>Ошибка размера файла</b>\n\n"
            "Максимальный размер файла: 50 МБ",
            parse_mode="HTML"
        )
        return
    
    # Обработка заявки
    await _process_ticket_completion(bot, message, ticket_id, message.document)

@user_router.message(F.text)
async def handle_vin_message(message: Message, bot: Bot) -> None:
    """Обработчик текстовых сообщений с VIN номерами.
    
    Args:
        message: Сообщение от пользователя
        bot: Экземпляр бота
    """
    # Проверяем что пользователь существует
    if not message.from_user:
        logger.error("❌ Сообщение без пользователя")
        await message.answer("❌ Ошибка: не удалось определить пользователя")
        return
    
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    text = message.text.strip() if message.text else ""
    
    logger.info("🔍 Обработка VIN сообщения", user_id=user_id, username=username, text=text, text_length=len(text))
    
    # Проверяем что текст не пустой
    if not text:
        logger.warning("⚠️ Пустое сообщение от пользователя", user_id=user_id)
        await message.answer("❌ Пожалуйста, отправьте VIN номер")
        return
    
    # Валидация VIN
    logger.info("🔍 Начинаем валидацию VIN", text=text)
    is_valid, error_message = VINValidator.validate(text)
    if not is_valid:
        logger.warning("⚠️ VIN не прошел валидацию", text=text, error=error_message)
        await message.answer(
            f"❌ <b>Ошибка валидации VIN</b>\n\n{error_message}\n\n"
            "💡 <b>Правильный формат:</b> 17 символов без I, O, Q\n"
            "📝 <b>Пример:</b> 1HGBH41JXMN109186",
            parse_mode="HTML"
        )
        return
    
    # Нормализация VIN
    logger.info("✅ VIN прошел валидацию, нормализуем", text=text)
    normalized_vin = VINValidator.normalize(text)
    logger.info("✅ VIN нормализован", normalized_vin=normalized_vin)
    
    # Проверяем, может ли пользователь сгенерировать отчет
    can_generate = await PaymentService.can_user_generate_report(user_id)
    if not can_generate:
        logger.info("💳 Пользователь не имеет активной подписки, предлагаем оплату", user_id=user_id)
        await _show_payment_options(message, bot, normalized_vin)
        return
    
    # Используем один отчет из подписки
    report_used = await PaymentService.use_user_report(user_id)
    if not report_used:
        logger.error("❌ Не удалось использовать отчет из подписки", user_id=user_id)
        await message.answer("❌ Ошибка: не удалось использовать отчет. Обратитесь в поддержку.")
        return
    
    # Создание заявки через db_adapter
    from src.db_adapter import db_adapter
    
    # Инициализация переменной для отправки в группу
    ticket_data = None
    
    try:
        # Создание новой заявки
        logger.info("🚀 Начинаем создание заявки", user_id=user_id, vin=normalized_vin, username=username)
        ticket_data = await db_adapter.create_ticket(normalized_vin, user_id, username)
        logger.info("✅ Заявка создана в базе данных", ticket_data=ticket_data)
        
        logger.info(
            "Создана новая заявка",
            ticket_id=ticket_data["id"],
            user_id=user_id,
            vin=normalized_vin
        )
        
        # Уведомление пользователя
        logger.debug("Отправляем уведомление пользователю", user_id=user_id, ticket_id=ticket_data['id'])
        await message.answer(
            f"✅ <b>Заявка принята!</b>\n\n"
            f"🆔 <b>Номер заявки:</b> #{ticket_data['id']}\n"
            f"🚗 <b>VIN:</b> <code>{normalized_vin}</code>\n"
            f"📊 <b>Статус:</b> в работе\n\n"
            f"⏰ <b>Время обработки:</b> 5-30 минут\n"
            f"📄 <b>Отчет будет отправлен</b> в личные сообщения",
            parse_mode="HTML"
        )
        logger.debug("Уведомление пользователю отправлено успешно", user_id=user_id)
        
    except Exception as e:
        logger.error("❌ КРИТИЧЕСКАЯ ОШИБКА создания заявки", user_id=user_id, vin=normalized_vin, username=username, error=str(e), exc_info=True)
        await message.answer(
            "❌ <b>Произошла ошибка</b>\n\n"
            "Не удалось создать заявку. Попробуйте позже или обратитесь в поддержку.",
            parse_mode="HTML"
        )
        return
    
    # Отправка в группу менеджеров
    if ticket_data is not None:
        await _send_ticket_to_managers(bot, ticket_data, username)


async def _send_ticket_to_managers(bot: Bot, ticket_data: dict, username: str) -> None:
    """Отправка карточки заявки в чат менеджеров."""
    try:
        ticket_text = (
            f"<b>🚗 Новая заявка на VIN-отчет</b>\n\n"
            f"<b>ID заявки:</b> #{ticket_data['id']}\n"
            f"<b>VIN:</b> <code>{ticket_data['vin']}</code>\n"
            f"<b>Пользователь:</b> @{username}\n"
            f"<b>Статус:</b> {ticket_data['status']}\n\n"
            f"<i>Нажмите кнопку ниже, чтобы взять заявку в работу</i>"
        )
        
        await bot.send_message(
            chat_id=settings.manager_chat_id,
            text=ticket_text,
            reply_markup=TicketKeyboards.get_take_keyboard(ticket_data['id']),
            parse_mode="HTML"
        )
        
        logger.info("✅ Заявка отправлена в группу менеджеров", ticket_id=ticket_data['id'])
        
    except Exception as e:
        logger.error("Ошибка отправки заявки менеджерам", error=str(e))


async def _process_ticket_completion(bot: Bot, message: Message, ticket_id: int, document) -> None:
    """Обработка завершения заявки."""
    from src.db_adapter import db_adapter
    
    manager_id = message.from_user.id
    manager_username = message.from_user.username or f"manager_{manager_id}"
    
    try:
        logger.debug("Начало обработки завершения заявки", ticket_id=ticket_id, manager_id=manager_id)
        
        # Получение заявки
        ticket_data = await db_adapter.get_ticket(ticket_id)
        logger.debug("Заявка получена из базы", ticket_data=ticket_data)
        
        if not ticket_data:
            await message.answer(
                f"❌ <b>Заявка не найдена</b>\n\n"
                f"Заявка №{ticket_id} не существует.",
                parse_mode="HTML"
            )
            return
        
        # Проверка статуса заявки
        if ticket_data['status'] == "DONE":
            await message.answer(
                f"⚠️ <b>Заявка уже завершена</b>\n\n"
                f"Заявка №{ticket_id} уже была закрыта.",
                parse_mode="HTML"
            )
            return
        
        # Обновление статуса заявки
        logger.debug("Обновление статуса заявки", ticket_id=ticket_id, status="DONE", assignee_id=manager_id)
        await db_adapter.update_ticket_status(ticket_id, "DONE", manager_id)
        
        logger.info(
            "Заявка завершена менеджером",
            ticket_id=ticket_id,
            manager_id=manager_id,
            manager_username=manager_username
        )
        
        # Отправка отчета пользователю
        logger.debug("Отправка отчета пользователю", ticket_id=ticket_id, user_id=ticket_data['user_id'])
        await _send_report_to_user(bot, ticket_data, document)
        
        # Подтверждение менеджеру
        logger.debug("Отправка подтверждения менеджеру", ticket_id=ticket_id)
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
            "❌ КРИТИЧЕСКАЯ ОШИБКА завершения заявки",
            ticket_id=ticket_id,
            manager_id=manager_id,
            error=str(e),
            exc_info=True
        )
        
        # Пытаемся отправить отчет пользователю даже при ошибке
        try:
            if 'ticket_data' in locals() and ticket_data:
                await _send_report_to_user(bot, ticket_data, document)
                logger.info("✅ Отчет отправлен пользователю несмотря на ошибку", 
                           ticket_id=ticket_id)
        except Exception as report_error:
            logger.error("❌ Не удалось отправить отчет пользователю", 
                        error=str(report_error))
        
        await message.answer(
            "❌ <b>Произошла ошибка</b>\n\n"
            "Не удалось завершить заявку. Попробуйте позже.",
            parse_mode="HTML"
        )


async def _send_report_to_user(bot: Bot, ticket_data: dict, document) -> None:
    """Отправка отчета пользователю."""
    try:
        # Уведомление о готовности отчета
        await bot.send_message(
            chat_id=ticket_data['user_id'],
            text=f"✅ <b>Заявка №{ticket_data['id']}: отчет готов!</b>\n\n"
                 f"🚗 <b>VIN:</b> <code>{ticket_data['vin']}</code>\n"
                 f"📄 <b>Ваш отчет (PDF)</b> прикреплен к сообщению ниже.",
            parse_mode="HTML"
        )
        
        # Пересылка документа пользователю
        await bot.send_document(
            chat_id=ticket_data['user_id'],
            document=document.file_id,
            caption="📄 Ваш отчет по VIN номеру",
            parse_mode="HTML"
        )
        
        logger.info(
            "Отчет отправлен пользователю",
            ticket_id=ticket_data['id'],
            user_id=ticket_data['user_id']
        )
        
    except Exception as e:
        logger.error(
            "Ошибка отправки отчета пользователю",
            ticket_id=ticket_data['id'],
            user_id=ticket_data['user_id'],
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


async def _show_payment_options(message: Message, bot: Bot, vin: str) -> None:
    """Показать опции оплаты пользователю.
    
    Args:
        message: Сообщение от пользователя
        bot: Экземпляр бота
        vin: VIN номер для которого нужен отчет
    """
    user_id = message.from_user.id if message.from_user else 0
    
    payment_text = (
        f"💳 <b>Оплата отчета по VIN: {vin}</b>\n\n"
        "Для получения отчета необходимо произвести оплату:\n\n"
        "💳 <b>1 отчет - $2.00</b>\n"
        "📦 <b>100 отчетов - $100.00</b> (экономия $100!)\n\n"
        "Выберите тариф:"
    )
    
    keyboard = PaymentKeyboards.get_payment_options_keyboard()
    
    # Сохраняем VIN в callback_data для последующего использования
    # Пока что используем простой подход - сохраняем в тексте сообщения
    
    await message.answer(
        payment_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    logger.info("💳 Показаны опции оплаты", user_id=user_id, vin=vin)


async def _handle_payment_selection(callback_query, payment_type: str) -> None:
    """Обработка выбора тарифа оплаты.
    
    Args:
        callback_query: Callback query от пользователя
        payment_type: Тип платежа (single или bulk)
    """
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or f"user_{user_id}"
    
    logger.info("💳 Пользователь выбрал тариф", user_id=user_id, payment_type=payment_type)
    
    if payment_type == "cancel":
        await callback_query.message.edit_text(
            "❌ Оплата отменена. Для получения отчета выберите тариф и произведите оплату.",
            reply_markup=PaymentKeyboards.get_payment_options_keyboard()
        )
        return
    
    # Создаем платеж
    try:
        payment = await PaymentService.create_payment(user_id, payment_type)
        
        # Показываем информацию о платеже
        price = PaymentService.format_price(payment.amount)
        description = PaymentService.get_payment_description(payment_type)
        
        payment_text = (
            f"💳 <b>Платеж создан</b>\n\n"
            f"📋 <b>Тариф:</b> {description}\n"
            f"💰 <b>Сумма:</b> {price}\n"
            f"🆔 <b>ID платежа:</b> {payment.id}\n\n"
            f"⚠️ <b>Внимание:</b> Это демо-версия!\n"
            f"Для завершения платежа нажмите кнопку подтверждения ниже.\n"
            f"В реальной версии здесь будет интеграция с платежной системой."
        )
        
        keyboard = PaymentKeyboards.get_payment_confirmation_keyboard(payment_type, payment.id)
        
        await callback_query.message.edit_text(
            payment_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
        logger.info("💳 Платеж создан", payment_id=payment.id, user_id=user_id, payment_type=payment_type)
        
    except Exception as e:
        logger.error("❌ Ошибка создания платежа", user_id=user_id, error=str(e))
        await callback_query.answer("❌ Ошибка создания платежа. Попробуйте еще раз.")


async def _handle_payment_confirmation(callback_query, payment_id: int) -> None:
    """Обработка подтверждения платежа.
    
    Args:
        callback_query: Callback query от пользователя
        payment_id: ID платежа
    """
    user_id = callback_query.from_user.id
    
    logger.info("💳 Подтверждение платежа", payment_id=payment_id, user_id=user_id)
    
    try:
        # Завершаем платеж
        success = await PaymentService.complete_payment(payment_id)
        
        if success:
            # Получаем информацию о подписке
            subscription = await PaymentService.get_user_subscription(user_id)
            
            success_text = (
                f"✅ <b>Платеж успешно завершен!</b>\n\n"
                f"🎉 Ваша подписка активирована!\n"
                f"📊 <b>Доступно отчетов:</b> {subscription.reports_remaining}\n"
                f"📈 <b>Всего куплено:</b> {subscription.total_reports}\n\n"
                f"Теперь вы можете отправлять VIN номера для получения отчетов!"
            )
            
            await callback_query.message.edit_text(
                success_text,
                parse_mode="HTML"
            )
            
            logger.info("✅ Платеж завершен успешно", payment_id=payment_id, user_id=user_id)
        else:
            await callback_query.answer("❌ Ошибка завершения платежа. Обратитесь в поддержку.")
            
    except Exception as e:
        logger.error("❌ Ошибка подтверждения платежа", payment_id=payment_id, user_id=user_id, error=str(e))
        await callback_query.answer("❌ Ошибка подтверждения платежа. Обратитесь в поддержку.")


async def _handle_payment_cancellation(callback_query, payment_id: int) -> None:
    """Обработка отмены платежа.
    
    Args:
        callback_query: Callback query от пользователя
        payment_id: ID платежа
    """
    user_id = callback_query.from_user.id
    
    logger.info("❌ Отмена платежа", payment_id=payment_id, user_id=user_id)
    
    await callback_query.message.edit_text(
        "❌ Платеж отменен.\n\nДля получения отчета выберите тариф и произведите оплату.",
        reply_markup=PaymentKeyboards.get_payment_options_keyboard()
    )
