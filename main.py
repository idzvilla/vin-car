#!/usr/bin/env python3
"""Точка входа для VIN Report Bot."""

import asyncio
import os
import sys
from src.bot import main

def check_single_instance():
    """Проверка, что запущен только один экземпляр бота."""
    pid_file = "/tmp/vin_bot.pid"
    
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                old_pid = int(f.read().strip())
            
            # Проверяем, жив ли процесс
            try:
                os.kill(old_pid, 0)
                print(f"❌ Бот уже запущен (PID: {old_pid})")
                sys.exit(1)
            except OSError:
                # Процесс не существует, удаляем старый PID файл
                os.remove(pid_file)
        except (ValueError, FileNotFoundError):
            os.remove(pid_file)
    
    # Создаем новый PID файл
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))

if __name__ == "__main__":
    check_single_instance()
    try:
        asyncio.run(main())
    finally:
        # Удаляем PID файл при завершении
        pid_file = "/tmp/vin_bot.pid"
        if os.path.exists(pid_file):
            os.remove(pid_file)
