from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from models import Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_url: str = "sqlite+aiosqlite:///starwars.db"):
        self.engine = create_async_engine(db_url, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def close(self):
        await self.engine.dispose()

    async def save_character(self, character_data: dict):
        """Сохранение персонажа с проверкой на дубликаты"""
        from models import Character
        
        async with self.async_session() as session:
            async with session.begin():
                # Проверяем существование
                result = await session.execute(
                    text("SELECT id FROM characters WHERE character_id = :char_id"),
                    {"char_id": character_data['character_id']}
                )
                if result.fetchone():
                    logger.info(f"⏭️ Character {character_data['name']} already exists, skipping")
                    return False
                
                character = Character(**character_data)
                session.add(character)
                logger.info(f"✅ Saved: {character_data['name']}")
                return True

    async def get_stats(self):
        async with self.async_session() as session:
            result = await session.execute(text("SELECT COUNT(*) FROM characters"))
            count = result.scalar()
            logger.info(f"📊 Total characters in database: {count}")
            return count
