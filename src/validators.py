"""Валидаторы для входных данных."""

from __future__ import annotations

import re
from typing import Optional

from loguru import logger


class VINValidator:
    """Валидатор VIN номеров."""
    
    # Регулярное выражение для VIN: 17 символов, исключая I, O, Q
    VIN_PATTERN = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")
    
    # Символы, которые не могут быть в VIN
    FORBIDDEN_CHARS = {"I", "O", "Q"}
    
    @classmethod
    def validate(cls, vin: str) -> tuple[bool, Optional[str]]:
        """Валидация VIN номера.
        
        Args:
            vin: VIN номер для валидации
            
        Returns:
            Кортеж (валидный, сообщение_об_ошибке)
        """
        if not vin:
            return False, "VIN номер не может быть пустым"
        
        # Очистка от пробелов и приведение к верхнему регистру
        cleaned_vin = vin.strip().upper()
        
        # Проверка длины
        if len(cleaned_vin) != 17:
            return False, "VIN номер должен содержать ровно 17 символов"
        
        # Проверка на запрещенные символы
        forbidden_found = set(cleaned_vin) & cls.FORBIDDEN_CHARS
        if forbidden_found:
            return False, f"VIN номер содержит запрещенные символы: {', '.join(forbidden_found)}"
        
        # Проверка по регулярному выражению
        if not cls.VIN_PATTERN.match(cleaned_vin):
            return False, "VIN номер содержит недопустимые символы"
        
        logger.debug("VIN номер прошел валидацию", vin=cleaned_vin)
        return True, None
    
    @classmethod
    def normalize(cls, vin: str) -> str:
        """Нормализация VIN номера.
        
        Args:
            vin: Исходный VIN номер
            
        Returns:
            Нормализованный VIN номер
        """
        return vin.strip().upper()
    
    @classmethod
    def is_valid(cls, vin: str) -> bool:
        """Проверка валидности VIN номера.
        
        Args:
            vin: VIN номер для проверки
            
        Returns:
            True если VIN валидный, False иначе
        """
        is_valid_vin, _ = cls.validate(vin)
        return is_valid_vin


class UserInputValidator:
    """Валидатор пользовательского ввода."""
    
    @staticmethod
    def validate_user_id(user_id: int) -> tuple[bool, Optional[str]]:
        """Валидация ID пользователя.
        
        Args:
            user_id: ID пользователя для валидации
            
        Returns:
            Кортеж (валидный, сообщение_об_ошибке)
        """
        if not isinstance(user_id, int):
            return False, "ID пользователя должен быть числом"
        
        if user_id <= 0:
            return False, "ID пользователя должен быть положительным числом"
        
        return True, None
    
    @staticmethod
    def validate_chat_id(chat_id: int) -> tuple[bool, Optional[str]]:
        """Валидация ID чата.
        
        Args:
            chat_id: ID чата для валидации
            
        Returns:
            Кортеж (валидный, сообщение_об_ошибке)
        """
        if not isinstance(chat_id, int):
            return False, "ID чата должен быть числом"
        
        return True, None
    
    @staticmethod
    def validate_ticket_id(ticket_id: int) -> tuple[bool, Optional[str]]:
        """Валидация ID заявки.
        
        Args:
            ticket_id: ID заявки для валидации
            
        Returns:
            Кортеж (валидный, сообщение_об_ошибке)
        """
        if not isinstance(ticket_id, int):
            return False, "ID заявки должен быть числом"
        
        if ticket_id <= 0:
            return False, "ID заявки должен быть положительным числом"
        
        return True, None


class MessageValidator:
    """Валидатор сообщений."""
    
    @staticmethod
    def validate_text_length(text: str, max_length: int = 4096) -> tuple[bool, Optional[str]]:
        """Валидация длины текста.
        
        Args:
            text: Текст для валидации
            max_length: Максимальная длина текста
            
        Returns:
            Кортеж (валидный, сообщение_об_ошибке)
        """
        if not text:
            return False, "Текст не может быть пустым"
        
        if len(text) > max_length:
            return False, f"Текст слишком длинный (максимум {max_length} символов)"
        
        return True, None
    
    @staticmethod
    def validate_document_size(file_size: int, max_size: int = 50 * 1024 * 1024) -> tuple[bool, Optional[str]]:
        """Валидация размера документа.
        
        Args:
            file_size: Размер файла в байтах
            max_size: Максимальный размер файла в байтах
            
        Returns:
            Кортеж (валидный, сообщение_об_ошибке)
        """
        if file_size <= 0:
            return False, "Размер файла должен быть положительным"
        
        if file_size > max_size:
            max_size_mb = max_size // (1024 * 1024)
            return False, f"Файл слишком большой (максимум {max_size_mb} МБ)"
        
        return True, None





