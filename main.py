#!/usr/bin/env python3
import asyncio
import os
import sys
from src.bot import main

def check_single_instance():
    pid_file = "/tmp/vin_bot.pid"
    
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                old_pid = int(f.read().strip())
            
            try:
                os.kill(old_pid, 0)
                print(f"❌ Бот уже запущен (PID: {old_pid})")
                sys.exit(1)
            except OSError:
                os.remove(pid_file)
        except (ValueError, FileNotFoundError):
            os.remove(pid_file)
    
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))

if __name__ == "__main__":
    check_single_instance()
    try:
        asyncio.run(main())
    finally:
        pid_file = "/tmp/vin_bot.pid"
        if os.path.exists(pid_file):
            os.remove(pid_file)
