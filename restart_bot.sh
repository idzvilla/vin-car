#!/bin/bash

echo "🔄 Полная перезагрузка VIN Report Bot..."

# Останавливаем все процессы Python
echo "⏹️ Останавливаем все процессы..."
pkill -f "python3 main.py" 2>/dev/null || true
pkill -f "python main.py" 2>/dev/null || true
pkill -f "python.*main" 2>/dev/null || true

# Удаляем PID файл
echo "🧹 Очищаем PID файл..."
rm -f /tmp/vin_bot.pid

# Ждем 3 секунды
echo "⏳ Ждем 3 секунды..."
sleep 3

# Проверяем, что процессы остановлены
if pgrep -f "python.*main" > /dev/null; then
    echo "❌ Процессы все еще запущены, принудительно завершаем..."
    pkill -9 -f "python.*main" 2>/dev/null || true
    sleep 2
fi

# Запускаем бота
echo "🚀 Запускаем бота..."
python3 main.py

echo "✅ Готово!"



