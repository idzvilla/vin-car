# 🤖 VIN Report Bot - Руководство по работе

## 📋 Обзор системы

VIN Report Bot - это Telegram бот для автоматизированной обработки заявок на получение отчетов по VIN номерам автомобилей. Система работает по принципу "пользователь → бот → менеджер → отчет".

## 🔄 Принцип работы

### 1. Пользователь отправляет VIN
- Пользователь отправляет VIN номер (17 символов) боту
- Система валидирует VIN (проверяет формат, исключает I, O, Q)
- Проверяется отсутствие дублирующих заявок

### 2. Создание заявки
- Создается запись в базе данных со статусом "NEW"
- Пользователь получает номер заявки и время обработки
- Заявка автоматически отправляется в чат менеджеров

### 3. Обработка менеджером
- Менеджер видит карточку заявки с кнопкой "Взять заявку"
- После взятия заявки статус меняется на "TAKEN"
- Менеджер готовит PDF отчет

### 4. Завершение заявки
- Менеджер отправляет PDF отчет (2 способа):
  - Ответ на карточку заявки с PDF
  - Команда `/done <номер_заявки>` + PDF
- Статус меняется на "DONE"
- Отчет автоматически отправляется пользователю

## 🧠 Логика работы бота

### Обработка сообщений пользователя

```python
# 1. Получение сообщения
@user_router.message(F.text)
async def handle_vin_message(message: Message, bot: Bot):
    text = message.text.strip()
    
    # 2. Валидация VIN
    is_valid, error = VINValidator.validate(text)
    if not is_valid:
        await message.answer(f"❌ Ошибка: {error}")
        return
    
    # 3. Нормализация VIN
    normalized_vin = VINValidator.normalize(text)
    
    # 4. Проверка дублирования
    existing_ticket = await check_existing_ticket(normalized_vin, user_id)
    if existing_ticket:
        await show_existing_ticket_status(message, existing_ticket)
        return
    
    # 5. Создание заявки
    ticket = await create_ticket(normalized_vin, user_id)
    
    # 6. Уведомление пользователя
    await notify_user_about_ticket(message, ticket)
    
    # 7. Отправка в чат менеджеров
    await send_ticket_to_managers(bot, ticket)
```

### Обработка действий менеджера

```python
# 1. Взятие заявки
@callback_router.callback_query(lambda c: c.data.startswith("take_ticket:"))
async def handle_take_ticket(callback: CallbackQuery):
    ticket_id = extract_ticket_id(callback.data)
    
    # Обновление статуса заявки
    ticket.status = "TAKEN"
    ticket.assignee_id = manager_id
    await session.commit()
    
    # Обновление карточки заявки
    await update_ticket_card(callback.message, ticket)

# 2. Завершение заявки
@manager_router.message(F.document)
async def handle_document_reply(message: Message):
    # Извлечение номера заявки из ответа
    ticket_id = extract_ticket_id_from_reply(message)
    
    # Валидация PDF
    if not is_valid_pdf(message.document):
        await message.answer("❌ Отправьте PDF файл")
        return
    
    # Завершение заявки
    await complete_ticket(ticket_id, message.document)
```

### Алгоритм валидации VIN

```python
class VINValidator:
    VIN_PATTERN = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")
    FORBIDDEN_CHARS = {"I", "O", "Q"}
    
    @classmethod
    def validate(cls, vin: str) -> tuple[bool, Optional[str]]:
        # 1. Проверка на пустоту
        if not vin:
            return False, "VIN номер не может быть пустым"
        
        # 2. Очистка и нормализация
        cleaned_vin = vin.strip().upper()
        
        # 3. Проверка длины
        if len(cleaned_vin) != 17:
            return False, "VIN номер должен содержать ровно 17 символов"
        
        # 4. Проверка запрещенных символов
        forbidden_found = set(cleaned_vin) & cls.FORBIDDEN_CHARS
        if forbidden_found:
            return False, f"Запрещенные символы: {', '.join(forbidden_found)}"
        
        # 5. Проверка по регулярному выражению
        if not cls.VIN_PATTERN.match(cleaned_vin):
            return False, "VIN номер содержит недопустимые символы"
        
        return True, None
```

### Состояния заявки (State Machine)

```python
# Переходы между состояниями
NEW → TAKEN    # Менеджер взял заявку
TAKEN → DONE   # Менеджер отправил отчет
DONE → (финальное состояние)

# Проверки перед переходами
def can_be_taken(ticket):
    return ticket.status == "NEW"

def can_be_done(ticket):
    return ticket.status in ("NEW", "TAKEN")
```

### Обработка ошибок

```python
# 1. Ошибки валидации
try:
    is_valid, error = VINValidator.validate(vin)
    if not is_valid:
        await handle_validation_error(message, error)
        return
except Exception as e:
    await handle_system_error(message, "Ошибка валидации")

# 2. Ошибки базы данных
try:
    async with get_db_session() as session:
        # Операции с БД
        await session.commit()
except Exception as e:
    logger.error("Database error", error=str(e))
    await handle_database_error(message)

# 3. Ошибки отправки сообщений
try:
    await bot.send_message(chat_id, text)
except Exception as e:
    logger.error("Send message error", error=str(e))
    # Сохранение в очередь для повторной отправки
```

### Логирование и мониторинг

```python
# Структурированное логирование
logger.info(
    "Создана новая заявка",
    ticket_id=ticket.id,
    user_id=user_id,
    vin=normalized_vin,
    status="NEW"
)

logger.error(
    "Ошибка создания заявки",
    user_id=user_id,
    error=str(e),
    vin=vin
)

# Метрики для мониторинга
- Количество созданных заявок
- Время обработки заявок
- Количество ошибок
- Активность пользователей
```

### Асинхронная обработка

```python
# Параллельная обработка сообщений
@user_router.message(F.text)
async def handle_vin_message(message: Message, bot: Bot):
    # Создание задачи для обработки
    task = asyncio.create_task(process_vin_request(message, bot))
    
    # Не блокируем основной поток
    await task

# Обработка множественных заявок
async def process_multiple_tickets():
    tasks = []
    for ticket in pending_tickets:
        task = asyncio.create_task(process_ticket(ticket))
        tasks.append(task)
    
    # Ожидание завершения всех задач
    await asyncio.gather(*tasks)
```

## 🏗️ Архитектура

```
Пользователь → VIN → Валидация → База данных → Менеджеры → PDF → Пользователь
     ↓              ↓              ↓              ↓           ↓
  Telegram      Валидаторы    SQLAlchemy     Callback     Отправка
   Bot API      (17 символов)   (SQLite)      кнопки      файлов
```

## 📁 Структура проекта

```
src/
├── bot.py              # Основной класс бота
├── db.py               # Подключение к базе данных
├── models.py           # Модели данных (Ticket)
├── settings.py         # Настройки приложения
├── validators.py       # Валидаторы (VIN, пользовательский ввод)
├── keyboards.py        # Клавиатуры для интерфейса
└── handlers/
    ├── user.py         # Обработчики пользователей
    ├── manager.py      # Обработчики менеджеров
    └── callbacks.py    # Обработчики кнопок
```

## 🗄️ База данных

### Таблица `tickets`
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | Integer | Уникальный ID заявки (автоинкремент) |
| `vin` | String(17) | VIN номер автомобиля |
| `user_id` | BigInteger | ID пользователя Telegram |
| `status` | String(10) | Статус: NEW, TAKEN, DONE |
| `assignee_id` | BigInteger | ID назначенного менеджера |
| `created_at` | DateTime | Время создания заявки |
| `updated_at` | DateTime | Время последнего обновления |

## 📊 Статусы заявок

| Статус | Описание | Действия |
|--------|----------|----------|
| **NEW** | Новая заявка | Менеджер может взять заявку |
| **TAKEN** | Назначена менеджеру | Менеджер готовит отчет |
| **DONE** | Завершена | Отчет отправлен пользователю |

## 🔧 Настройка

### Переменные окружения (.env)
```env
BOT_TOKEN=your_telegram_bot_token
MANAGER_CHAT_ID=your_manager_chat_id
DATABASE_URL=sqlite:///./vin_reports.db
LOG_LEVEL=INFO
MAX_FILE_SIZE=52428800  # 50MB в байтах
```

### Запуск
```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск бота
python main.py
```

## 👥 Роли пользователей

### Пользователь
- Отправляет VIN номер боту
- Получает номер заявки
- Получает PDF отчет в личные сообщения

### Менеджер
- Видит новые заявки в чате менеджеров
- Может взять заявку на себя
- Отправляет готовый PDF отчет
- Получает подтверждения об отправке

## 🎯 Команды бота

### Для пользователей
- `/start` - Запуск бота и приветствие
- `/help` - Справка по использованию
- `VIN номер` - Отправка VIN для создания заявки

### Для менеджеров
- `/done <номер_заявки>` - Завершение заявки с PDF

## 🔍 Валидация VIN

VIN номер должен соответствовать следующим требованиям:
- ✅ Ровно 17 символов
- ✅ Только буквы A-H, J-N, P-R, T-Z и цифры 0-9
- ❌ Запрещены буквы I, O, Q
- ✅ Автоматическое приведение к верхнему регистру

**Примеры:**
- ✅ `1HGBH41JXMN109186` - валидный
- ❌ `1HGBH41JXMN10918` - слишком короткий
- ❌ `1HGBH41JXMN109186O` - содержит запрещенную букву O

## 📱 Интерфейс

### Клавиатуры для пользователей
- **Стартовая**: "Как получить отчет?", "Поддержка"
- **Помощь**: "Назад"

### Клавиатуры для менеджеров
- **Новая заявка**: "Взять заявку", "Как завершить?"
- **Назначенная заявка**: "Как завершить?"
- **Подсказки**: "Отправить PDF в ответ", "Использовать команду /done"

## 🚨 Обработка ошибок

### Ошибки валидации VIN
- Неверная длина
- Запрещенные символы
- Некорректный формат

### Ошибки заявок
- Дублирование заявок
- Заявка не найдена
- Неверный статус заявки

### Ошибки файлов
- Превышение размера (максимум 50 МБ)
- Неверный формат (только PDF)

## 📝 Логирование

Логи сохраняются в:
- **Консоль**: INFO уровень и выше
- **Файл**: `logs/bot.log` (DEBUG уровень)
- **Ротация**: ежедневно, хранение 30 дней

## 🔒 Безопасность

- Валидация всех входных данных
- Проверка прав доступа к командам
- Ограничение размера файлов
- Логирование всех действий

## 🚀 Развертывание

### Docker
```bash
# Сборка образа
docker build -t vin-report-bot .

# Запуск контейнера
docker-compose up -d
```

### Системные требования
- Python 3.8+
- SQLite (или PostgreSQL для продакшена)
- 50 МБ свободного места для логов

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи в `logs/bot.log`
2. Убедитесь в корректности настроек
3. Проверьте доступность базы данных
4. Обратитесь к разработчику

---

**Версия документации:** 1.0  
**Последнее обновление:** $(date)  
**Автор:** VIN Report Bot Team
