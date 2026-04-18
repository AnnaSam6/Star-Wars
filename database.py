from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
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
        """Сохранение без дублей"""
        from models import Character
        
        async with self.async_session() as session:
            # Проверка на дубль
            result = await session.execute(
                text("SELECT id FROM characters WHERE character_id = :char_id"),
                {"char_id": character_data['character_id']}
            )
            if result.fetchone():
                logger.info(f"⏭️  Skip duplicate: {character_data['name']}")
                return False
            
            character = Character(**character_data)
            session.add(character)
            await session.commit()
            logger.info(f"✅ Saved: {character_data['name']}")
            return True

    async def get_all(self):
        """Получение всех персонажей для проверки"""
        async with self.async_session() as session:
            result = await session.execute(text("SELECT * FROM characters ORDER BY character_id"))
            return result.fetchall()

    async def get_stats(self):
        async with self.async_session() as session:
            result = await session.execute(text("SELECT COUNT(*) FROM characters"))
            count = result.scalar()
            logger.info(f"📊 Total in DB: {count}")
            return count
