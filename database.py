from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from models import Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Database:
    """Асинхронный класс для работы с базой данных"""

    def __init__(self, db_url: str = "sqlite+aiosqlite:///starwars.db"):
        self.engine = create_async_engine(db_url, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def init_db(self):
        """Инициализация базы данных (создание таблиц)"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")

    async def close(self):
        """Закрытие соединения с базой данных"""
        await self.engine.dispose()
        logger.info("Database connection closed")

    async def save_character(self, character_data: dict):
        """Сохранение персонажа в базу данных"""
        from models import Character

        async with self.async_session() as session:
            async with session.begin():
                # Проверяем, существует ли уже персонаж
                stmt = text("SELECT * FROM characters WHERE character_id = :char_id")
                result = await session.execute(stmt, {"char_id": character_data['character_id']})
                existing = result.fetchone()

                if existing:
                    logger.info(f"Character {character_data['name']} already exists, skipping")
                    return False

                # Создаем нового персонажа
                character = Character(**character_data)
                session.add(character)
                logger.info(f"Saved character: {character_data['name']} (ID: {character_data['character_id']})")
                return True

    async def get_all_characters(self):
        """Получение всех персонажей из базы данных"""
        from models import Character

        async with self.async_session() as session:
            result = await session.execute(
                text("SELECT * FROM characters ORDER BY character_id")
            )
            characters = result.fetchall()
            return characters

    async def get_statistics(self):
        """Получение статистики по загруженным данным"""
        async with self.async_session() as session:
            result = await session.execute(text("SELECT COUNT(*) FROM characters"))
            count = result.scalar()

            result = await session.execute(
                text("SELECT COUNT(DISTINCT gender) FROM characters WHERE gender IS NOT NULL AND gender != ''")
            )
            gender_count = result.scalar()

            return {
                "total_characters": count,
                "unique_genders": gender_count
            }
