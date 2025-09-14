"""Тесты для валидаторов."""

import pytest

from src.validators import VINValidator, UserInputValidator, MessageValidator


class TestVINValidator:
    """Тесты для валидатора VIN номеров."""
    
    def test_valid_vin(self):
        """Тест валидного VIN номера."""
        valid_vins = [
            "1HGBH41JXMN109186",
            "1FTFW1ET5DFC12345",
            "WBAFR7C50BC123456",
            "JM1BK32F381234567"
        ]
        
        for vin in valid_vins:
            is_valid, error = VINValidator.validate(vin)
            assert is_valid, f"VIN {vin} должен быть валидным: {error}"
    
    def test_invalid_vin_length(self):
        """Тест VIN с неверной длиной."""
        invalid_vins = [
            "1HGBH41JXMN10918",  # 16 символов
            "1HGBH41JXMN1091867",  # 18 символов
            "",  # пустой
            "123"  # слишком короткий
        ]
        
        for vin in invalid_vins:
            is_valid, error = VINValidator.validate(vin)
            assert not is_valid, f"VIN {vin} должен быть невалидным"
            assert "17 символов" in error or "пустым" in error
    
    def test_invalid_vin_forbidden_chars(self):
        """Тест VIN с запрещенными символами."""
        invalid_vins = [
            "1HGBH41JXMN10918I",  # содержит I
            "1HGBH41JXMN10918O",  # содержит O
            "1HGBH41JXMN10918Q",  # содержит Q
            "1HGBH41JXMN10918i",  # содержит i (строчная)
        ]
        
        for vin in invalid_vins:
            is_valid, error = VINValidator.validate(vin)
            assert not is_valid, f"VIN {vin} должен быть невалидным"
            assert "запрещенные символы" in error
    
    def test_invalid_vin_special_chars(self):
        """Тест VIN с специальными символами."""
        invalid_vins = [
            "1HGBH41JXMN109-86",  # содержит дефис
            "1HGBH41JXMN109 86",  # содержит пробел
            "1HGBH41JXMN109@86",  # содержит @
            "1HGBH41JXMN109#86",  # содержит #
        ]
        
        for vin in invalid_vins:
            is_valid, error = VINValidator.validate(vin)
            assert not is_valid, f"VIN {vin} должен быть невалидным"
    
    def test_normalize_vin(self):
        """Тест нормализации VIN."""
        test_cases = [
            (" 1HGBH41JXMN109186 ", "1HGBH41JXMN109186"),
            ("1hgbh41jxmn109186", "1HGBH41JXMN109186"),
            ("  1HGBH41JXMN109186  ", "1HGBH41JXMN109186"),
        ]
        
        for input_vin, expected in test_cases:
            result = VINValidator.normalize(input_vin)
            assert result == expected, f"Нормализация {input_vin} должна дать {expected}, получено {result}"
    
    def test_is_valid_method(self):
        """Тест метода is_valid."""
        assert VINValidator.is_valid("1HGBH41JXMN109186") is True
        assert VINValidator.is_valid("1HGBH41JXMN10918I") is False
        assert VINValidator.is_valid("") is False


class TestUserInputValidator:
    """Тесты для валидатора пользовательского ввода."""
    
    def test_valid_user_id(self):
        """Тест валидного ID пользователя."""
        valid_ids = [1, 123, 999999999, 1234567890]
        
        for user_id in valid_ids:
            is_valid, error = UserInputValidator.validate_user_id(user_id)
            assert is_valid, f"User ID {user_id} должен быть валидным: {error}"
    
    def test_invalid_user_id(self):
        """Тест невалидного ID пользователя."""
        invalid_ids = [0, -1, -123, "123", None, 1.5]
        
        for user_id in invalid_ids:
            is_valid, error = UserInputValidator.validate_user_id(user_id)
            assert not is_valid, f"User ID {user_id} должен быть невалидным"
    
    def test_valid_chat_id(self):
        """Тест валидного ID чата."""
        valid_ids = [1, -1001234567890, 123456789]
        
        for chat_id in valid_ids:
            is_valid, error = UserInputValidator.validate_chat_id(chat_id)
            assert is_valid, f"Chat ID {chat_id} должен быть валидным: {error}"
    
    def test_invalid_chat_id(self):
        """Тест невалидного ID чата."""
        invalid_ids = ["123", None, 1.5]
        
        for chat_id in invalid_ids:
            is_valid, error = UserInputValidator.validate_chat_id(chat_id)
            assert not is_valid, f"Chat ID {chat_id} должен быть невалидным"
    
    def test_valid_ticket_id(self):
        """Тест валидного ID заявки."""
        valid_ids = [1, 123, 999999]
        
        for ticket_id in valid_ids:
            is_valid, error = UserInputValidator.validate_ticket_id(ticket_id)
            assert is_valid, f"Ticket ID {ticket_id} должен быть валидным: {error}"
    
    def test_invalid_ticket_id(self):
        """Тест невалидного ID заявки."""
        invalid_ids = [0, -1, -123, "123", None, 1.5]
        
        for ticket_id in invalid_ids:
            is_valid, error = UserInputValidator.validate_ticket_id(ticket_id)
            assert not is_valid, f"Ticket ID {ticket_id} должен быть невалидным"


class TestMessageValidator:
    """Тесты для валидатора сообщений."""
    
    def test_valid_text_length(self):
        """Тест валидной длины текста."""
        valid_texts = [
            "Hello",
            "A" * 1000,
            "A" * 4096,  # максимальная длина
        ]
        
        for text in valid_texts:
            is_valid, error = MessageValidator.validate_text_length(text)
            assert is_valid, f"Текст длиной {len(text)} должен быть валидным: {error}"
    
    def test_invalid_text_length(self):
        """Тест невалидной длины текста."""
        invalid_texts = [
            "",  # пустой
            "A" * 5000,  # слишком длинный
        ]
        
        for text in invalid_texts:
            is_valid, error = MessageValidator.validate_text_length(text)
            assert not is_valid, f"Текст длиной {len(text)} должен быть невалидным"
    
    def test_valid_document_size(self):
        """Тест валидного размера документа."""
        valid_sizes = [
            1024,  # 1KB
            1024 * 1024,  # 1MB
            50 * 1024 * 1024,  # 50MB (максимум)
        ]
        
        for size in valid_sizes:
            is_valid, error = MessageValidator.validate_document_size(size)
            assert is_valid, f"Размер {size} должен быть валидным: {error}"
    
    def test_invalid_document_size(self):
        """Тест невалидного размера документа."""
        invalid_sizes = [
            0,  # нулевой размер
            -1,  # отрицательный размер
            100 * 1024 * 1024,  # 100MB (слишком большой)
        ]
        
        for size in invalid_sizes:
            is_valid, error = MessageValidator.validate_document_size(size)
            assert not is_valid, f"Размер {size} должен быть невалидным"





