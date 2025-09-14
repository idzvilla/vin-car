#!/bin/bash

# Скрипт для развертывания VIN бота на VPS

set -e

echo "🚀 Развертывание VIN бота на сервере..."

# Проверяем, что мы на сервере
if [ -z "$BOT_TOKEN" ]; then
    echo "❌ Ошибка: BOT_TOKEN не установлен"
    echo "Установите переменные окружения:"
    echo "export BOT_TOKEN=your_bot_token"
    echo "export MANAGER_CHAT_ID=your_chat_id"
    exit 1
fi

# Обновляем систему
echo "📦 Обновление системы..."
sudo apt update && sudo apt upgrade -y

# Устанавливаем Docker
if ! command -v docker &> /dev/null; then
    echo "🐳 Установка Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

# Устанавливаем Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "🐳 Установка Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Создаем директорию для бота
BOT_DIR="/opt/vin-bot"
echo "📁 Создание директории $BOT_DIR..."
sudo mkdir -p $BOT_DIR
sudo chown $USER:$USER $BOT_DIR

# Клонируем репозиторий
echo "📥 Клонирование репозитория..."
cd $BOT_DIR
if [ -d ".git" ]; then
    git pull origin main
else
    git clone https://github.com/idzvilla/vin-car.git .
fi

# Создаем файл окружения
echo "⚙️ Создание конфигурации..."
cat > env_config << EOF
BOT_TOKEN=$BOT_TOKEN
MANAGER_CHAT_ID=$MANAGER_CHAT_ID
DATABASE_URL=sqlite:///./data/vin_reports.db
LOG_LEVEL=INFO
USE_SUPABASE=false
MAX_FILE_SIZE=52428800
RATE_LIMIT_PER_MINUTE=10
EOF

# Создаем директории
mkdir -p logs data

# Собираем и запускаем контейнер
echo "🔨 Сборка и запуск контейнера..."
docker-compose -f docker-compose.production.yml up -d --build

# Проверяем статус
echo "✅ Проверка статуса..."
sleep 10
docker-compose -f docker-compose.production.yml ps

echo ""
echo "🎉 Развертывание завершено!"
echo "📝 Логи: docker-compose -f docker-compose.production.yml logs -f"
echo "🛑 Остановка: docker-compose -f docker-compose.production.yml down"
echo "🔄 Перезапуск: docker-compose -f docker-compose.production.yml restart"

