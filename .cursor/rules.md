# Правила кодирования VIN Report Bot

## Общие принципы

### Type Hints
- Все функции должны иметь type hints
- Использовать `from __future__ import annotations` для forward references
- Импортировать типы из `typing` и `typing_extensions`
- Использовать `Optional[T]` вместо `Union[T, None]`

### Логирование
- Использовать `loguru` для всех логов
- Структурированное логирование с контекстом
- Уровни: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Не логировать чувствительные данные (PDF, токены)

### Обработка ошибок
- Все async функции должны обрабатывать исключения
- Использовать try/except с конкретными типами исключений
- Логировать ошибки с контекстом
- Возвращать понятные сообщения пользователю

## Структура кода

### Импорты
```python
# Стандартная библиотека
import asyncio
from datetime import datetime
from typing import Optional

# Сторонние библиотеки
from aiogram import Bot, Dispatcher
from sqlalchemy import select

# Локальные импорты
from .models import Ticket
from .settings import Settings
```

### Функции
```python
async def create_ticket(
    vin: str,
    user_id: int,
    session: AsyncSession
) -> Ticket:
    """Создать новую заявку.
    
    Args:
        vin: VIN номер автомобиля
        user_id: ID пользователя Telegram
        session: Сессия базы данных
        
    Returns:
        Созданная заявка
        
    Raises:
        ValueError: Если VIN невалидный
        SQLAlchemyError: При ошибке БД
    """
    # Реализация
```

### Классы
```python
class TicketService:
    """Сервис для работы с заявками."""
    
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
    
    async def create(self, vin: str, user_id: int) -> Ticket:
        """Создать заявку."""
        # Реализация
```

## Обработка ошибок

### Паттерны обработки
```python
try:
    result = await some_operation()
    logger.info("Operation completed", result_id=result.id)
    return result
except ValidationError as e:
    logger.warning("Validation failed", error=str(e))
    raise ValueError("Неверные данные") from e
except SQLAlchemyError as e:
    logger.error("Database error", error=str(e))
    raise RuntimeError("Ошибка базы данных") from e
except Exception as e:
    logger.error("Unexpected error", error=str(e))
    raise
```

### Retry логика
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def send_message_with_retry(bot: Bot, chat_id: int, text: str) -> None:
    """Отправить сообщение с повторными попытками."""
    await bot.send_message(chat_id, text)
```

## Конфигурация

### Environment Variables
- Все настройки через переменные окружения
- Использовать `pydantic-settings` для валидации
- Значения по умолчанию для разработки
- Обязательные переменные для продакшена

### Secrets
- Никогда не коммитить токены и пароли
- Использовать `.env` файлы локально
- Переменные окружения в продакшене
- Валидация наличия обязательных переменных

## База данных

### Сессии
- Использовать async context managers
- Закрывать сессии в finally блоках
- Обрабатывать rollback при ошибках

### Транзакции
```python
async with session.begin():
    ticket = Ticket(vin=vin, user_id=user_id)
    session.add(ticket)
    # Автоматический commit/rollback
```

### Запросы
- Использовать `select()` вместо `session.query()`
- Добавлять индексы для производительности
- Избегать N+1 запросов

## Telegram Bot

### Обработчики
- Один обработчик = одна ответственность
- Валидация входных данных
- Обработка ошибок с понятными сообщениями
- Логирование действий пользователей

### Callbacks
- Валидация callback data
- Проверка прав доступа
- Обработка устаревших callback'ов

### Сообщения
- Экранирование HTML в сообщениях
- Использование markdown для форматирования
- Локализация на русский язык

## Тестирование

### Unit тесты
- Тестировать бизнес-логику
- Мокать внешние зависимости
- Покрытие > 80%

### Интеграционные тесты
- Тестировать взаимодействие компонентов
- Использовать тестовую БД
- Проверять полные сценарии

## Производительность

### Асинхронность
- Использовать async/await везде
- Избегать блокирующих операций
- Параллельные запросы где возможно

### Кеширование
- Кешировать часто используемые данные
- TTL для кеша
- Инвалидация при изменениях

## Безопасность

### Валидация
- Валидировать все входные данные
- Санитизация пользовательского ввода
- Ограничение размера файлов

### Авторизация
- Проверка прав доступа
- Валидация chat_id
- Защита от CSRF

## Документация

### Docstrings
- Описание функции/класса
- Args и Returns
- Raises для исключений
- Примеры использования

### Комментарии
- Объяснять сложную бизнес-логику
- TODO для будущих улучшений
- FIXME для известных проблем

## Git

### Коммиты
- Один коммит = одна логическая единица
- Понятные сообщения коммитов
- Использовать conventional commits

### Ветки
- `main` - стабильная версия
- `develop` - разработка
- `feature/*` - новые функции
- `hotfix/*` - исправления





