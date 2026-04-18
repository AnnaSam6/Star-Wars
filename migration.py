"""Скрипт для создания схемы базы данных"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from models import Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_migration():
    """Создание всех таблиц в базе данных"""
    engine = create_async_engine("sqlite+aiosqlite:///starwars.db", echo=True)
    
    async with engine.begin() as conn:
        # Создаем все таблицы
        await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database tables created successfully")
    
    await engine.dispose()
    logger.info("Migration completed!")


def main():
    asyncio.run(run_migration())


if __name__ == "__main__":
    main()
