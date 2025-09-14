#!/bin/bash

echo "🔄 Обновление GitHub репозитория..."

# Проверяем статус git
echo "📋 Проверка статуса git..."
git status

# Добавляем все изменения
echo "➕ Добавление изменений..."
git add .

# Создаем коммит
echo "💾 Создание коммита..."
git commit -m "Clean up project: remove unnecessary files and code

- Removed duplicate env files (.env)
- Cleaned up code comments and docstrings
- Removed test files and unused modules
- Simplified project structure
- Updated env.example with placeholder values
- Project is now clean and ready for deployment"

# Отправляем на GitHub
echo "🚀 Отправка на GitHub..."
git push origin main

echo "✅ Обновление завершено!"

