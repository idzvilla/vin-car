#!/usr/bin/env python3
"""Сброс webhook для текущего токена."""

import asyncio
import aiohttp

BOT_TOKEN = "7427373200:AAFzwSoAMMhy0DO5pzaqLS8_8c6Nyxi2zkU"

async def reset_webhook():
    """Сброс webhook."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url) as response:
            result = await response.json()
            print(f"Webhook reset result: {result}")
            return result.get('ok', False)

async def main():
    """Сброс webhook."""
    print("🔄 Сброс webhook...")
    
    success = await reset_webhook()
    if success:
        print("✅ Webhook сброшен успешно")
    else:
        print("❌ Ошибка сброса webhook")

if __name__ == "__main__":
    asyncio.run(main())





