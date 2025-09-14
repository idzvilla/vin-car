#!/bin/bash

# Скрипт для управления VIN ботом

BOT_PID_FILE="/tmp/vin_bot.pid"
LOG_FILE="bot.log"

case "$1" in
    start)
        echo "🚀 Запуск VIN бота..."
        
        # Проверяем, не запущен ли уже бот
        if [ -f "$BOT_PID_FILE" ]; then
            PID=$(cat "$BOT_PID_FILE")
            if ps -p "$PID" > /dev/null 2>&1; then
                echo "❌ Бот уже запущен (PID: $PID)"
                exit 1
            else
                echo "🧹 Удаляем старый PID файл"
                rm -f "$BOT_PID_FILE"
            fi
        fi
        
        # Останавливаем все процессы бота
        pkill -f "python.*main.py" 2>/dev/null || true
        sleep 2
        
        # Запускаем бота
        nohup python3 main.py > "$LOG_FILE" 2>&1 &
        echo $! > "$BOT_PID_FILE"
        
        echo "✅ Бот запущен (PID: $(cat $BOT_PID_FILE))"
        echo "📝 Логи: $LOG_FILE"
        ;;
        
    stop)
        echo "🛑 Остановка VIN бота..."
        
        if [ -f "$BOT_PID_FILE" ]; then
            PID=$(cat "$BOT_PID_FILE")
            if ps -p "$PID" > /dev/null 2>&1; then
                kill "$PID"
                echo "✅ Бот остановлен (PID: $PID)"
            else
                echo "⚠️  Процесс не найден"
            fi
            rm -f "$BOT_PID_FILE"
        fi
        
        # Дополнительно убиваем все процессы
        pkill -f "python.*main.py" 2>/dev/null || true
        ;;
        
    restart)
        echo "🔄 Перезапуск VIN бота..."
        $0 stop
        sleep 2
        $0 start
        ;;
        
    status)
        if [ -f "$BOT_PID_FILE" ]; then
            PID=$(cat "$BOT_PID_FILE")
            if ps -p "$PID" > /dev/null 2>&1; then
                echo "✅ Бот работает (PID: $PID)"
                echo "⏰ Время запуска: $(ps -o lstart= -p $PID)"
            else
                echo "❌ Бот не работает (PID файл есть, но процесс не найден)"
            fi
        else
            echo "❌ Бот не запущен"
        fi
        ;;
        
    logs)
        echo "📝 Показываем логи бота..."
        if [ -f "$LOG_FILE" ]; then
            tail -f "$LOG_FILE"
        else
            echo "❌ Файл логов не найден"
        fi
        ;;
        
    *)
        echo "Использование: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Команды:"
        echo "  start   - Запустить бота в фоновом режиме"
        echo "  stop    - Остановить бота"
        echo "  restart - Перезапустить бота"
        echo "  status  - Показать статус бота"
        echo "  logs    - Показать логи в реальном времени"
        exit 1
        ;;
esac

