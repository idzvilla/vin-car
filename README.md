# VIN Report Bot

Telegram бот для обработки VIN отчетов с человеческим контролем. Пользователи отправляют VIN номера, менеджеры обрабатывают заявки и отправляют PDF отчеты.

## 🚀 Возможности

- **Валидация VIN номеров** - проверка формата и корректности
- **Система заявок** - создание, назначение и отслеживание заявок
- **Человеческий контроль** - менеджеры обрабатывают заявки вручную
- **Автоматическая отправка отчетов** - PDF отчеты отправляются пользователям
- **Уведомления** - статус заявок в реальном времени
- **Безопасность** - валидация доступа и данных

## 📋 Требования

- Python 3.11+
- Telegram Bot Token
- SQLite (по умолчанию) или PostgreSQL
- Docker (опционально)

## 🛠 Установка

### Локальная установка

1. **Клонирование репозитория**
   ```bash
   git clone <repository-url>
   cd CarFax
   ```

2. **Установка зависимостей**
   ```bash
   # Используя pip
   pip install -e .
   
   # Или используя uv
   uv pip install -e .
   ```

3. **Настройка окружения**
   ```bash
   cp env.example .env
   # Отредактируйте .env файл
   ```

4. **Запуск бота**

   **Обычный запуск (для разработки):**
   ```bash
   python main.py
   ```

   **Фоновый запуск (для продакшена):**
   ```bash
   # Запуск в фоновом режиме
   ./run_bot_background.sh
   
   # Или используйте менеджер бота
   ./bot_manager.sh start
   ```

   **Управление ботом:**
   ```bash
   ./bot_manager.sh start    # Запустить
   ./bot_manager.sh stop     # Остановить
   ./bot_manager.sh restart  # Перезапустить
   ./bot_manager.sh status   # Статус
   ./bot_manager.sh logs     # Логи
   ```

### Docker установка

1. **Клонирование и настройка**
   ```bash
   git clone <repository-url>
   cd CarFax
   cp env.example .env
   # Отредактируйте .env файл
   ```

2. **Запуск с Docker Compose**
   ```bash
   docker-compose up -d
   ```

## ⚙️ Конфигурация

### Переменные окружения

Создайте файл `.env` на основе `env.example`:

```env
# Обязательные переменные
BOT_TOKEN=your_bot_token_here
MANAGER_CHAT_ID=your_manager_chat_id_here

# Опциональные переменные
DATABASE_URL=sqlite+aiosqlite:///./vin_reports.db
LOG_LEVEL=INFO
MAX_FILE_SIZE=52428800  # 50MB
```

### Получение BOT_TOKEN

1. Создайте бота через [@BotFather](https://t.me/BotFather)
2. Получите токен и добавьте в `.env`

### Получение MANAGER_CHAT_ID

1. Добавьте бота в группу/канал менеджеров
2. Отправьте сообщение в группу
3. Используйте [@userinfobot](https://t.me/userinfobot) для получения ID чата
4. Добавьте ID в `.env`

## 📖 Использование

### Для пользователей

1. **Запуск бота** - `/start`
2. **Отправка VIN** - отправьте 17-символьный VIN номер
3. **Ожидание отчета** - получите PDF в личные сообщения

### Для менеджеров

1. **Получение заявки** - бот отправляет карточку заявки в чат менеджеров
2. **Назначение заявки** - нажмите "Взять заявку"
3. **Отправка отчета** - ответьте на карточку заявки PDF документом
4. **Альтернативно** - используйте команду `/done <номер_заявки>` + PDF

## 🏗 Архитектура

### Структура проекта

```
CarFax/
├── src/
│   ├── handlers/          # Обработчики сообщений
│   │   ├── user.py       # Пользовательские команды
│   │   ├── manager.py    # Команды менеджеров
│   │   └── callbacks.py  # Callback обработчики
│   ├── models.py         # Модели базы данных
│   ├── db.py            # Настройка БД
│   ├── settings.py      # Конфигурация
│   ├── validators.py    # Валидаторы
│   ├── keyboards.py     # Клавиатуры
│   └── bot.py          # Основной файл бота
├── main.py              # Точка входа
├── pyproject.toml       # Зависимости
├── Dockerfile          # Docker образ
├── docker-compose.yml  # Docker Compose
└── README.md          # Документация
```

### Workflow

1. **Пользователь** отправляет VIN → создается заявка
2. **Бот** уведомляет пользователя и отправляет карточку менеджерам
3. **Менеджер** назначает заявку себе
4. **Менеджер** отправляет PDF отчет
5. **Бот** пересылает отчет пользователю и закрывает заявку

## 🗄 База данных

### SQLite (по умолчанию)

База данных создается автоматически при первом запуске.

### PostgreSQL

Для использования PostgreSQL:

1. Установите `asyncpg`:
   ```bash
   pip install asyncpg
   ```

2. Измените `DATABASE_URL` в `.env`:
   ```env
   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/vin_reports
   ```

### Схема таблиц

```sql
CREATE TABLE tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vin TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('NEW', 'TAKEN', 'DONE')),
    assignee_id INTEGER NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL
);
```

## 🔧 Разработка

### Установка для разработки

```bash
# Клонирование
git clone <repository-url>
cd CarFax

# Установка зависимостей
pip install -e ".[dev]"

# Установка pre-commit hooks
pre-commit install
```

### Запуск тестов

```bash
pytest
```

### Линтинг

```bash
ruff check .
black .
mypy .
```

## 🐳 Docker

### Сборка образа

```bash
docker build -t vin-report-bot .
```

### Запуск контейнера

```bash
docker run -d \
  --name vin-report-bot \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  vin-report-bot
```

### Docker Compose

```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f bot

# Остановка
docker-compose down
```

## 📊 Мониторинг

### Логи

Логи сохраняются в директории `logs/`:
- `bot.log` - основные логи приложения
- Ротация каждый день
- Сжатие старых логов

### Статус заявок

- `NEW` - новая заявка
- `TAKEN` - назначена менеджеру
- `DONE` - завершена

## 🔒 Безопасность

- Валидация всех входных данных
- Проверка прав доступа для команд менеджеров
- Ограничение размера файлов
- Не логирование чувствительных данных

## 🚨 Устранение неполадок

### Частые проблемы

1. **Бот не отвечает**
   - Проверьте токен бота
   - Убедитесь, что бот добавлен в чат менеджеров

2. **Ошибки базы данных**
   - Проверьте права доступа к файлу БД
   - Убедитесь, что директория `data/` существует

3. **Не работает отправка PDF**
   - Проверьте размер файла (максимум 50MB)
   - Убедитесь, что файл в формате PDF

### Логи

```bash
# Просмотр логов
tail -f logs/bot.log

# Docker логи
docker-compose logs -f bot
```

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для функции
3. Внесите изменения
4. Добавьте тесты
5. Создайте Pull Request

## 📄 Лицензия

MIT License

## 📞 Поддержка

- Создайте Issue в GitHub
- Напишите в Telegram: @support_username
- Email: support@example.com





