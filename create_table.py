#!/usr/bin/env python3
"""Создание таблицы в Supabase через API."""

import asyncio
import httpx
from src.supabase_config import supabase_settings

async def create_table():
    """Создание таблицы tickets в Supabase."""
    url = f"{supabase_settings.supabase_url}/rest/v1/rpc/exec_sql"
    headers = {
        "apikey": supabase_settings.supabase_key,
        "Authorization": f"Bearer {supabase_settings.supabase_key}",
        "Content-Type": "application/json"
    }
    
    sql = """
    CREATE TABLE IF NOT EXISTS tickets (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        username VARCHAR(255),
        vin VARCHAR(17) NOT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'NEW',
        assignee_id BIGINT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    
    data = {"sql": sql}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=data)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(create_table())





