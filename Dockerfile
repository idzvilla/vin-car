# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Создаем пользователя для безопасности
RUN groupadd -r botuser && useradd -r -g botuser botuser

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем файлы зависимостей
COPY pyproject.toml ./

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -e .

# Копируем исходный код
COPY src/ ./src/
COPY main.py ./

# Создаем директории для логов и данных
RUN mkdir -p logs data && \
    chown -R botuser:botuser /app

# Переключаемся на пользователя botuser
USER botuser

# Устанавливаем переменные окружения
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Создаем volume для данных
VOLUME ["/app/data", "/app/logs"]

# Открываем порт (если понадобится для health check)
EXPOSE 8000

# Команда запуска
CMD ["python", "main.py"]
