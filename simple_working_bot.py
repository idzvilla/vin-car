#!/usr/bin/env python3
"""Простой рабочий бот с кнопками без базы данных."""

import asyncio
import re
from datetime import datetime
from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from src.settings import settings
from src.validators import VINValidator

# Создаем бота и диспетчер
bot = Bot(
    token=settings.bot_token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# Роутеры
user_router = Router()
callback_router = Router()

# Импорт для работы с базой данных
from src.db import init_db, get_db_session
from src.models import Ticket
from sqlalchemy import select

# Простое хранилище заявок в памяти (резервное)
tickets = {}
ticket_counter = 1

@user_router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Обработчик команды /start."""
    user_id = message.from_user.id
    username = message.from_user.username or "пользователь"
    
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
    
    await message.answer(welcome_text)

@user_router.message(F.text)
async def handle_vin_message(message: Message) -> None:
    """Обработчик текстовых сообщений с VIN номерами."""
    global ticket_counter
    
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    text = message.text.strip()
    
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
    
    # Проверка на дублирование
    for ticket in tickets.values():
        if ticket["vin"] == normalized_vin and ticket["user_id"] == user_id and ticket["status"] in ["NEW", "TAKEN"]:
            await message.answer(
                f"⚠️ <b>Заявка уже существует</b>\n\n"
                f"Заявка №{ticket['id']} с VIN <code>{normalized_vin}</code> "
                f"уже обрабатывается.\n\n"
                f"📊 <b>Статус:</b> {_get_status_text(ticket['status'])}",
                parse_mode="HTML"
            )
            return
    
    # Создание заявки в базе данных
    try:
        async with get_db_session() as session:
            ticket = Ticket(
                user_id=user_id,
                username=username,
                vin=normalized_vin,
                status="NEW",
                created_at=datetime.now()
            )
            session.add(ticket)
            await session.commit()
            await session.refresh(ticket)
            ticket_id = ticket.id
            
            logger.info(f"Заявка создана в БД: {ticket_id}")
            
    except Exception as e:
        logger.error(f"Ошибка создания заявки в БД: {e}")
        # Резервное создание в памяти
        ticket_id = ticket_counter
        ticket_counter += 1
        
        tickets[ticket_id] = {
            "id": ticket_id,
            "vin": normalized_vin,
            "user_id": user_id,
            "status": "NEW",
            "assignee_id": None,
            "created_at": datetime.now().strftime('%d.%m.%Y %H:%M')
        }
    
    # Уведомление пользователя
    await message.answer(
        f"✅ <b>Заявка принята!</b>\n\n"
        f"🆔 <b>Номер заявки:</b> #{ticket_id}\n"
        f"🚗 <b>VIN:</b> <code>{normalized_vin}</code>\n"
        f"📊 <b>Статус:</b> в работе\n\n"
        f"⏰ <b>Время обработки:</b> 5-30 минут\n"
        f"📄 <b>Отчет будет отправлен</b> в личные сообщения",
        parse_mode="HTML"
    )
    
    # Отправка карточки заявки в чат менеджеров
    await send_ticket_to_managers(ticket_id, username)

async def send_ticket_to_managers(ticket_id: int, username: str) -> None:
    """Отправка карточки заявки в чат менеджеров."""
    ticket = tickets[ticket_id]
    
    ticket_text = (
        f"🆕 <b>Новая заявка №{ticket['id']}</b>\n\n"
        f"👤 <b>От:</b> @{username} (ID: {ticket['user_id']})\n"
        f"🚗 <b>VIN:</b> <code>{ticket['vin']}</code>\n"
        f"📅 <b>Создана:</b> {ticket['created_at']}\n"
        f"📊 <b>Статус:</b> новая"
    )
    
    # Создаем клавиатуру
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 Взять заявку",
                    callback_data=f"take_ticket:{ticket_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❓ Как завершить?",
                    callback_data=f"done_hint:{ticket_id}"
                )
            ]
        ]
    )
    
    await bot.send_message(
        chat_id=settings.manager_chat_id,
        text=ticket_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@callback_router.callback_query(lambda c: c.data.startswith("take_ticket:"))
async def handle_take_ticket(callback: CallbackQuery) -> None:
    """Обработчик назначения заявки."""
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
    
    if ticket_id not in tickets:
        await callback.answer("❌ Заявка не найдена.")
        return
    
    ticket = tickets[ticket_id]
    
    # Проверка статуса заявки
    if ticket["status"] != "NEW":
        await callback.answer("❌ Заявка уже назначена или завершена.")
        return
    
    # Назначение заявки
    ticket["status"] = "TAKEN"
    ticket["assignee_id"] = callback.from_user.id
    
    manager_username = callback.from_user.username or f"manager_{callback.from_user.id}"
    
    # Обновление сообщения
    if callback.message:
        updated_text = (
            f"🆕 <b>Новая заявка №{ticket['id']}</b>\n\n"
            f"👤 <b>От:</b> @{manager_username} (ID: {ticket['user_id']})\n"
            f"🚗 <b>VIN:</b> <code>{ticket['vin']}</code>\n"
            f"📅 <b>Создана:</b> {ticket['created_at']}\n"
            f"📊 <b>Статус:</b> назначена\n"
            f"👨‍💼 <b>Назначена:</b> @{manager_username}"
        )
        
        # Обновляем клавиатуру
        updated_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="❓ Как завершить?",
                        callback_data=f"done_hint:{ticket_id}"
                    )
                ]
            ]
        )
        
        await callback.message.edit_text(
            text=updated_text,
            reply_markup=updated_keyboard,
            parse_mode="HTML"
        )
    
    await callback.answer("✅ Заявка назначена вам!")

@callback_router.callback_query(lambda c: c.data.startswith("done_hint:"))
async def handle_done_hint(callback: CallbackQuery) -> None:
    """Обработчик подсказки о завершении заявки."""
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
        parse_mode="HTML"
    )
    
    await callback.answer("💡 Инструкция отправлена!")

@user_router.message(F.document)
async def handle_document_reply(message: Message) -> None:
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
    await process_ticket_completion(message, ticket_id)

async def process_ticket_completion(message: Message, ticket_id: int) -> None:
    """Обработка завершения заявки."""
    manager_id = message.from_user.id
    manager_username = message.from_user.username or f"manager_{manager_id}"
    
    try:
        # Поиск заявки в базе данных
        async with get_db_session() as session:
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
    
            # Отправка отчета пользователю
            await send_report_to_user(ticket, message.document)
            
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
                    await message.reply_to_message.edit_reply_markup(reply_markup=None)
                except Exception as e:
                    logger.warning(f"Не удалось обновить карточку заявки: {e}")
                    
    except Exception as e:
        logger.error(f"Ошибка завершения заявки: {e}")
        await message.answer(
            "❌ <b>Произошла ошибка</b>\n\n"
            "Не удалось завершить заявку. Попробуйте позже.",
            parse_mode="HTML"
        )

async def send_report_to_user(ticket, document) -> None:
    """Отправка отчета пользователю."""
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
            caption="📄 Ваш отчет по VIN номеру",
            parse_mode="HTML"
        )
        
        logger.info(f"Отчет отправлен пользователю {ticket.user_id} для заявки {ticket.id}")
        
    except Exception as e:
        logger.error(f"Ошибка отправки отчета пользователю: {e}")

def _get_status_text(status: str) -> str:
    """Получение текстового представления статуса."""
    status_map = {
        "NEW": "новая",
        "TAKEN": "в работе",
        "DONE": "завершена"
    }
    return status_map.get(status, "неизвестно")

# Регистрация роутеров
dp.include_router(user_router)
dp.include_router(callback_router)

async def main():
    """Главная функция запуска бота."""
    print("🚀 Запуск VIN Report Bot...")
    
    # Инициализация базы данных
    try:
        await init_db()
        print("✅ База данных инициализирована")
    except Exception as e:
        print(f"⚠️ Ошибка инициализации БД: {e}")
        print("Бот будет работать с резервным хранилищем в памяти")
    
    # Получение информации о боте
    bot_info = await bot.get_me()
    print(f"✅ Бот запущен: @{bot_info.username}")
    
    # Запуск polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
