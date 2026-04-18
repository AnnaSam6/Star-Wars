import asyncio
import aiohttp
from typing import Dict, Any, List
import logging
from database import Database
from models import Base

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StarWarsLoader:
    """Полностью переработанный загрузчик с обогащением данных"""
    
    BASE_URL = "https://www.swapi.tech/api"
    
    def __init__(self, max_concurrent=10):
        self.max_concurrent = max_concurrent
        self.session = None
        self.cache = {}  # Кэш для уже загруженных сущностей

    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self

    async def __aexit__(self, *args):
        await self.session.close()

    async def fetch_with_retry(self, url: str, retries=3) -> Dict:
        """Запрос с повторными попытками"""
        for attempt in range(retries):
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.warning(f"HTTP {response.status} for {url}")
            except asyncio.TimeoutError:
                logger.warning(f"Timeout on attempt {attempt + 1} for {url}")
            except Exception as e:
                logger.warning(f"Error on attempt {attempt + 1}: {e}")
            
            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        return None

    async def get_planet_name(self, planet_url: str) -> str:
        """Получение НАЗВАНИЯ планеты по URL (а не сохранение URL)"""
        if not planet_url:
            return "unknown"
        
        if planet_url in self.cache:
            return self.cache[planet_url]
        
        data = await self.fetch_with_retry(planet_url)
        if data and 'result' in data:
            name = data['result']['properties'].get('name', 'unknown')
            self.cache[planet_url] = name
            return name
        return "unknown"

    async def get_names_from_urls(self, urls: List[str], entity_type: str) -> str:
        """Преобразование списка URL в строку названий через запятую"""
        if not urls:
            return ""
        
        names = []
        for url in urls[:5]:  # Ограничиваем для производительности
            if url in self.cache:
                names.append(self.cache[url])
            else:
                data = await self.fetch_with_retry(url)
                if data and 'result' in data:
                    name = data['result']['properties'].get('name', '')
                    if not name:
                        name = data['result']['properties'].get('title', '')
                    self.cache[url] = name
                    names.append(name)
                else:
                    names.append("unknown")
        
        return ", ".join(names)

    async def enrich_character(self, raw_data: Dict, char_id: int) -> Dict[str, Any]:
        """Обогащение данных персонажа: загрузка связанных сущностей"""
        properties = raw_data.get('result', {}).get('properties', {})
        
        # Получаем название планеты (НЕ URL!)
        homeworld_url = properties.get('homeworld', '')
        homeworld_name = await self.get_planet_name(homeworld_url)
        
        # Получаем названия связанных сущностей
        films = await self.get_names_from_urls(properties.get('films', []), 'films')
        species = await self.get_names_from_urls(properties.get('species', []), 'species')
        starships = await self.get_names_from_urls(properties.get('starships', []), 'starships')
        vehicles = await self.get_names_from_urls(properties.get('vehicles', []), 'vehicles')
        
        # Конвертация массы и роста
        mass = properties.get('mass', '')
        mass_float = None
        if mass and mass != 'unknown':
            try:
                mass_float = float(mass)
            except ValueError:
                pass
        
        height = properties.get('height', '')
        height_float = None
        if height and height != 'unknown':
            try:
                height_float = float(height)
            except ValueError:
                pass
        
        return {
            'character_id': char_id,
            'name': properties.get('name', 'Unknown'),
            'birth_year': properties.get('birth_year', ''),
            'eye_color': properties.get('eye_color', ''),
            'gender': properties.get('gender', ''),
            'hair_color': properties.get('hair_color', ''),
            'homeworld': homeworld_name,  # Здесь НАЗВАНИЕ, а не URL!
            'mass': mass_float,
            'skin_color': properties.get('skin_color', ''),
            'height': height_float,
            'films': films,
            'species': species,
            'starships': starships,
            'vehicles': vehicles,
            'url': properties.get('url', '')
        }

    async def get_total_count(self) -> int:
        """Получение общего количества персонажей"""
        data = await self.fetch_with_retry(f"{self.BASE_URL}/people")
        if data:
            return data.get('total_records', 0)
        return 0

    async def fetch_character(self, char_id: int) -> Dict:
        """Загрузка одного персонажа"""
        url = f"{self.BASE_URL}/people/{char_id}"
        return await self.fetch_with_retry(url)

    async def load_all_characters(self) -> List[Dict]:
        """Асинхронная загрузка ВСЕХ персонажей"""
        total = await self.get_total_count()
        logger.info(f"📊 Total characters to fetch: {total}")
        
        if total == 0:
            total = 83  # Примерное количество
        
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def fetch_one(char_id: int):
            async with semaphore:
                logger.info(f"🔄 Fetching character {char_id}...")
                data = await self.fetch_character(char_id)
                if data:
                    enriched = await self.enrich_character(data, char_id)
                    return enriched
                return None
        
        tasks = [fetch_one(i) for i in range(1, total + 1)]
        results = await asyncio.gather(*tasks)
        
        characters = [c for c in results if c is not None]
        logger.info(f"✅ Fetched {len(characters)} characters successfully")
        return characters


async def main():
    logger.info("🚀 Starting Star Wars data loader...")
    
    db = Database()
    
    try:
        async with StarWarsLoader(max_concurrent=10) as loader:
            characters = await loader.load_all_characters()
            
            saved = 0
            for char in characters:
                success = await db.save_character(char)
                if success:
                    saved += 1
            
            await db.get_stats()
            logger.info(f"✨ Done! Saved {saved} new characters")
            
            # Вывод примера
            if characters:
                sample = characters[0]
                logger.info(f"\n📝 Example of enriched data:")
                logger.info(f"   Name: {sample['name']}")
                logger.info(f"   Homeworld: {sample['homeworld']}")  # Должно быть название, а не URL
                logger.info(f"   Films: {sample['films']}")
                
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
