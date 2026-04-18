#!/usr/bin/env python3
"""Скрипт миграции - создание схемы БД"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from models import Base

async def run_migration():
    """Безопасное создание таблиц"""
    engine = create_async_engine("sqlite+aiosqlite:///starwars.db", echo=True)
    
    async with engine.begin() as conn:
        # Проверяем существование таблицы
        result = await conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='characters'"
        ))
        exists = result.fetchone()
        
        if exists:
            print("⚠️  Table 'characters' already exists")
            response = input("Do you want to recreate it? (y/N): ")
            if response.lower() == 'y':
                print("🗑️  Dropping existing table...")
                await conn.execute(text("DROP TABLE IF EXISTS characters"))
                print("📦 Creating new table...")
                await conn.run_sync(Base.metadata.create_all)
                print("✅ Migration completed - table recreated!")
            else:
                print("✅ Keeping existing table")
        else:
            print("📦 Creating new table...")
            await conn.run_sync(Base.metadata.create_all)
            print("✅ Migration completed - table created!")
    
    await engine.dispose()

def main():
    asyncio.run(run_migration())

if __name__ == "__main__":
    main()
