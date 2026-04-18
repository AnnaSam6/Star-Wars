import asyncio
import aiohttp
import logging
from typing import List, Dict, Any
from database import Database
from models import Character

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StarWarsAPI:
    """Класс для асинхронной работы с API Star Wars"""

    BASE_URL = "https://www.swapi.tech/api"
    PEOPLE_URL = f"{BASE_URL}/people"

    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def get_total_people_count(self) -> int:
        """Получение общего количества персонажей"""
        async with self.session.get(self.PEOPLE_URL) as response:
            data = await response.json()
            # API возвращает общее количество в total_records
            total = data.get('total_records', 0)
            logger.info(f"Total characters to fetch: {total}")
            return total

    async def fetch_character(self, character_id: int) -> Dict[str, Any]:
        """Асинхронное получение данных о персонаже по ID"""
        url = f"{self.PEOPLE_URL}/{character_id}"
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return self.parse_character_data(data, character_id)
                else:
                    logger.warning(f"Failed to fetch character {character_id}: HTTP {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching character {character_id}: {e}")
            return None

    def parse_character_data(self, data: Dict, character_id: int) -> Dict[str, Any]:
        """Парсинг данных персонажа из API в формат для БД"""
        try:
            properties = data.get('result', {}).get('properties', {})
            result = data.get('result', {})

            # Конвертируем массу из строки в число
            mass_str = properties.get('mass', '')
            mass = None
            if mass_str and mass_str != 'unknown':
                try:
                    mass = float(mass_str)
                except ValueError:
                    mass = None

            # Конвертируем рост из строки в число
            height_str = properties.get('height', '')
            height = None
            if height_str and height_str != 'unknown':
                try:
                    height = float(height_str)
                except ValueError:
                    height = None

            return {
                'character_id': int(character_id),
                'name': properties.get('name', 'Unknown'),
                'birth_year': properties.get('birth_year', ''),
                'eye_color': properties.get('eye_color', ''),
                'gender': properties.get('gender', ''),
                'hair_color': properties.get('hair_color', ''),
                'homeworld': properties.get('homeworld', ''),
                'mass': mass,
                'skin_color': properties.get('skin_color', ''),
                'height': height,
                'api_created': properties.get('created', ''),
                'api_edited': properties.get('edited', '')
            }
        except Exception as e:
            logger.error(f"Error parsing character {character_id}: {e}")
            return None

    async def fetch_all_characters(self) -> List[Dict[str, Any]]:
        """Асинхронное получение всех персонажей с контролем конкурентности"""
        total = await self.get_total_people_count()
        if total == 0:
            # Если API не вернул total_records, пробуем получить до 100 персонажей
            total = 100

        characters = []
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def fetch_with_semaphore(char_id: int):
            async with semaphore:
                character = await self.fetch_character(char_id)
                if character:
                    return character
                return None

        # Создаем задачи для всех персонажей
        tasks = [fetch_with_semaphore(i) for i in range(1, total + 1)]
        results = await asyncio.gather(*tasks)

        # Фильтруем None результаты
        characters = [char for char in results if char is not None]
        logger.info(f"Successfully fetched {len(characters)} characters")
        return characters


class StarWarsLoader:
    """Класс для загрузки данных в базу данных"""

    def __init__(self, database: Database):
        self.database = database

    async def load_characters(self, characters: List[Dict[str, Any]]):
        """Асинхронная загрузка персонажей в БД"""
        saved_count = 0
        for character in characters:
            success = await self.database.save_character(character)
            if success:
                saved_count += 1

        logger.info(f"Loaded {saved_count} new characters into database")
        return saved_count


async def main():
    """Главная асинхронная функция"""
    logger.info("Starting Star Wars data loading process...")

    # Инициализация базы данных
    db = Database()
    await db.init_db()

    try:
        # Загрузка данных из API
        async with StarWarsAPI(max_concurrent=15) as api:
            logger.info("Fetching characters from SWAPI...")
            characters = await api.fetch_all_characters()

            if not characters:
                logger.error("No characters fetched from API")
                return

            logger.info(f"Fetched {len(characters)} characters from API")

            # Загрузка в базу данных
            loader = StarWarsLoader(db)
            saved = await loader.load_characters(characters)

            # Вывод статистики
            stats = await db.get_statistics()
            logger.info("=" * 50)
            logger.info("LOADING COMPLETED!")
            logger.info(f"Total characters in API: {len(characters)}")
            logger.info(f"New characters saved: {saved}")
            logger.info(f"Total characters in database: {stats['total_characters']}")
            logger.info(f"Unique genders: {stats['unique_genders']}")
            logger.info("=" * 50)

            # Вывод первых 5 персонажей для проверки
            logger.info("\nFirst 5 characters in database:")
            all_chars = await db.get_all_characters()
            for i, char in enumerate(all_chars[:5]):
                logger.info(f"  {i+1}. {char[2]} (ID: {char[1]}) - {char[5]}")  # name, character_id, gender

    except Exception as e:
        logger.error(f"Error in main process: {e}")
    finally:
        await db.close()


def run():
    """Функция для запуска асинхронного кода"""
    asyncio.run(main())


if __name__ == "__main__":
    run()
