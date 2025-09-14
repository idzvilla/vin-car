# 🚀 Развертывание VIN бота

Инструкции по развертыванию бота на различных платформах.

## 🌐 Варианты развертывания

### 1. VPS/Сервер (рекомендуется)

#### Быстрый деплой на VPS

1. **Подготовьте VPS:**
   - Ubuntu 20.04+ или Debian 11+
   - Минимум 1GB RAM, 1 CPU
   - SSH доступ

2. **Запустите деплой:**
   ```bash
   # На вашем компьютере
   export BOT_TOKEN="your_bot_token"
   export MANAGER_CHAT_ID="your_chat_id"
   
   # Скопируйте скрипт на сервер
   scp deploy.sh user@your-server:/tmp/
   
   # Запустите на сервере
   ssh user@your-server
   chmod +x /tmp/deploy.sh
   /tmp/deploy.sh
   ```

#### Ручной деплой на VPS

1. **Подключитесь к серверу:**
   ```bash
   ssh user@your-server
   ```

2. **Установите зависимости:**
   ```bash
   sudo apt update
   sudo apt install -y git docker.io docker-compose
   sudo usermod -aG docker $USER
   ```

3. **Клонируйте репозиторий:**
   ```bash
   git clone https://github.com/idzvilla/vin-car.git
   cd vin-car
   ```

4. **Настройте окружение:**
   ```bash
   cp env.example env_config
   nano env_config  # Отредактируйте настройки
   ```

5. **Запустите бота:**
   ```bash
   docker-compose -f docker-compose.production.yml up -d
   ```

### 2. Railway (простой деплой)

1. **Подключите GitHub:**
   - Зайдите на [railway.app](https://railway.app)
   - Подключите GitHub аккаунт
   - Выберите репозиторий `vin-car`

2. **Настройте переменные:**
   - `BOT_TOKEN` - токен бота
   - `MANAGER_CHAT_ID` - ID чата менеджеров
   - `DATABASE_URL` - URL базы данных (Railway предоставит PostgreSQL)

3. **Деплой:**
   - Railway автоматически соберет и запустит бота
   - Бот будет работать 24/7

### 3. Render (бесплатный тариф)

1. **Создайте аккаунт:**
   - Зайдите на [render.com](https://render.com)
   - Подключите GitHub

2. **Создайте Web Service:**
   - Выберите репозиторий `vin-car`
   - Выберите Docker
   - Укажите Dockerfile path: `./Dockerfile`

3. **Настройте переменные:**
   - `BOT_TOKEN`
   - `MANAGER_CHAT_ID`
   - `DATABASE_URL=sqlite:///./data/vin_reports.db`

4. **Деплой:**
   - Render автоматически развернет бота

### 4. Heroku

1. **Установите Heroku CLI:**
   ```bash
   # macOS
   brew install heroku/brew/heroku
   
   # Ubuntu
   curl https://cli-assets.heroku.com/install.sh | sh
   ```

2. **Логин и создание приложения:**
   ```bash
   heroku login
   heroku create your-vin-bot
   ```

3. **Настройте переменные:**
   ```bash
   heroku config:set BOT_TOKEN=your_bot_token
   heroku config:set MANAGER_CHAT_ID=your_chat_id
   heroku config:set DATABASE_URL=sqlite:///./data/vin_reports.db
   ```

4. **Деплой:**
   ```bash
   git push heroku main
   ```

### 5. Fly.io

1. **Установите Fly CLI:**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Логин и создание приложения:**
   ```bash
   fly auth login
   fly launch
   ```

3. **Настройте переменные:**
   ```bash
   fly secrets set BOT_TOKEN=your_bot_token
   fly secrets set MANAGER_CHAT_ID=your_chat_id
   ```

4. **Деплой:**
   ```bash
   fly deploy
   ```

## 🔧 Управление после деплоя

### Docker Compose (VPS)

```bash
# Статус
docker-compose -f docker-compose.production.yml ps

# Логи
docker-compose -f docker-compose.production.yml logs -f

# Перезапуск
docker-compose -f docker-compose.production.yml restart

# Остановка
docker-compose -f docker-compose.production.yml down

# Обновление
git pull
docker-compose -f docker-compose.production.yml up -d --build
```

### Railway

- Логи: в панели Railway
- Переменные: Settings → Variables
- Перезапуск: Deployments → Redeploy

### Render

- Логи: в панели Render
- Переменные: Environment
- Перезапуск: Manual Deploy

## 📊 Мониторинг

### Проверка работы бота

```bash
# Проверка через Telegram API
curl "https://api.telegram.org/bot$BOT_TOKEN/getMe"

# Проверка логов
tail -f logs/bot.log
```

### Автоматический перезапуск

Все платформы поддерживают автоматический перезапуск при сбоях:
- **Docker**: `restart: unless-stopped`
- **Railway**: автоматически
- **Render**: автоматически
- **Heroku**: автоматически

## 🔒 Безопасность

### Рекомендации для продакшена

1. **Используйте HTTPS** для webhook (если нужен)
2. **Ограничьте доступ** к серверу по SSH ключам
3. **Регулярно обновляйте** систему и зависимости
4. **Мониторьте логи** на предмет ошибок
5. **Делайте бэкапы** базы данных

### Переменные окружения

Никогда не коммитьте секретные данные в git:
- Используйте `.env` файлы (не в git)
- Используйте переменные окружения платформы
- Используйте секреты (Railway, Fly.io)

## 🆘 Устранение неполадок

### Бот не отвечает

1. Проверьте токен бота
2. Проверьте логи на ошибки
3. Убедитесь, что бот добавлен в чат менеджеров

### Ошибки базы данных

1. Проверьте права доступа к файлу БД
2. Убедитесь, что директория `data/` существует
3. Проверьте переменную `DATABASE_URL`

### Проблемы с Docker

1. Проверьте, что Docker запущен
2. Проверьте логи контейнера
3. Пересоберите образ: `docker-compose build --no-cache`

## 📈 Масштабирование

### Для высоких нагрузок

1. **Используйте PostgreSQL** вместо SQLite
2. **Добавьте Redis** для кэширования
3. **Используйте load balancer** для нескольких экземпляров
4. **Мониторьте ресурсы** сервера

### Рекомендуемые ресурсы

- **1-10 пользователей**: 1GB RAM, 1 CPU
- **10-100 пользователей**: 2GB RAM, 2 CPU
- **100+ пользователей**: 4GB RAM, 4 CPU

