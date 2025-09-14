#!/usr/bin/env python3
"""Сброс webhook нового бота."""

import asyncio
import aiohttp

NEW_BOT_TOKEN = "8332460974:AAEKslmXVYbQYriYz5yOWsKbmPz_vMFKkQ4"

async def reset_new_bot():
    """Сброс webhook нового бота."""
    url = f"https://api.telegram.org/bot{NEW_BOT_TOKEN}/deleteWebhook"
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url) as response:
            result = await response.json()
            print(f"Webhook reset result: {result}")
            return result.get('ok', False)

async def main():
    """Сброс webhook нового бота."""
    print("🔄 Сброс webhook нового бота...")
    
    success = await reset_new_bot()
    if success:
        print("✅ Webhook нового бота сброшен успешно")
    else:
        print("❌ Ошибка сброса webhook")

if __name__ == "__main__":
    asyncio.run(main())





