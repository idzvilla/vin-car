#!/bin/bash
echo "Запуск VIN Report Bot..."
python3 main.py &
echo "Бот запущен в фоновом режиме"
echo "PID: $!"
echo "Для остановки: kill $!"




