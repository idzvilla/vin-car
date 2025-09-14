#!/bin/bash

# Скрипт для запуска бота в фоновом режиме
# Бот будет работать даже после закрытия терминала

echo "🚀 Запуск VIN бота в фоновом режиме..."

# Останавливаем все существующие процессы бота
pkill -f "python.*main.py" 2>/dev/null || true
sleep 2

# Удаляем старый PID файл
rm -f /tmp/vin_bot.pid

# Запускаем бота в фоновом режиме с nohup
nohup python3 main.py > bot.log 2>&1 &

# Сохраняем PID процесса
echo $! > /tmp/vin_bot.pid

echo "✅ Бот запущен в фоновом режиме!"
echo "📋 PID: $(cat /tmp/vin_bot.pid)"
echo "📝 Логи: bot.log"
echo ""
echo "Команды для управления:"
echo "  Остановить: pkill -f 'python.*main.py'"
echo "  Посмотреть логи: tail -f bot.log"
echo "  Проверить статус: ps aux | grep main.py"

