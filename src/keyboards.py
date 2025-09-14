from __future__ import annotations

from typing import Optional

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from loguru import logger


class TicketKeyboards:
    @staticmethod
    def get_take_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
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
        
        logger.debug("Создана клавиатура для назначения заявки", ticket_id=ticket_id)
        return keyboard
    
    @staticmethod
    def get_taken_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="❓ Как завершить?",
                        callback_data=f"done_hint:{ticket_id}"
                    )
                ]
            ]
        )
        
        logger.debug("Создана клавиатура для назначенной заявки", ticket_id=ticket_id)
        return keyboard
    
    @staticmethod
    def get_done_hint_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📤 Отправить PDF в ответ на это сообщение",
                        callback_data=f"send_pdf_hint:{ticket_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="💬 Или используйте команду /done",
                        callback_data=f"command_hint:{ticket_id}"
                    )
                ]
            ]
        )
        
        logger.debug("Создана клавиатура с подсказкой", ticket_id=ticket_id)
        return keyboard
    
    @staticmethod
    def get_empty_keyboard() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[])


class MainKeyboards:
    @staticmethod
    def get_start_keyboard() -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="ℹ️ Как получить отчет?",
                        callback_data="help_info"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📞 Поддержка",
                        callback_data="support_info"
                    )
                ]
            ]
        )
        
        logger.debug("Создана стартовая клавиатура")
        return keyboard
    
    @staticmethod
    def get_help_keyboard() -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Назад",
                        callback_data="back_to_start"
                    )
                ]
            ]
        )
        
        logger.debug("Создана клавиатура помощи")
        return keyboard


class ManagerKeyboards:
    @staticmethod
    def get_manager_actions_keyboard() -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📊 Статистика",
                        callback_data="manager_stats"
                    ),
                    InlineKeyboardButton(
                        text="📋 Все заявки",
                        callback_data="manager_tickets"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⚙️ Настройки",
                        callback_data="manager_settings"
                    )
                ]
            ]
        )
        
        logger.debug("Создана клавиатура действий менеджера")
        return keyboard

