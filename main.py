#!/usr/bin/env python3
import asyncio
import aiohttp
from typing import Dict, Any, List
import logging
from database import Database

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StarWarsLoader:
    BASE_URL = "https://www.swapi.tech/api"
    
    def __init__(self, max_concurrent=10):
        self.max_concurrent = max_concurrent
        self.session = None
        self.planet_cache = {}  # Кэш для планет
        self.film_cache = {}    # Кэш для фильмов
        self.species_cache = {} # Кэш для видов
        self.ship_cache = {}    # Кэш для кораблей

    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self

    async def __aexit__(self, *args):
        await self.session.close()

    async def fetch(self, url: str, retries=3) -> Dict:
        """Запрос с повторными попытками"""
        for attempt in range(retries):
            try:
                async with self.session.get(url) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    logger.warning(f"HTTP {resp.status} for {url}")
            except asyncio.TimeoutError:
                logger.warning(f"Timeout {url}, attempt {attempt+1}")
            except Exception as e:
                logger.warning(f"Error {url}: {e}, attempt {attempt+1}")
            
            if attempt < retries - 1:
                await asyncio.sleep(1 * (attempt + 1))
        return None

    async def get_planet_name(self, planet_url: str) -> str:
        """Получаем НАЗВАНИЕ планеты (не URL!)"""
        if not planet_url:
            return "unknown"
        
        if planet_url in self.planet_cache:
            return self.planet_cache[planet_url]
        
        data = await self.fetch(planet_url)
        if data and 'result' in data:
            name = data['result']['properties'].get('name', 'unknown')
            self.planet_cache[planet_url] = name
            logger.debug(f"🌍 Planet: {name}")
            return name
        return "unknown"

    async def get_film_names(self, film_urls: List[str]) -> str:
        """Получаем НАЗВАНИЯ фильмов через запятую"""
        if not film_urls:
            return ""
        
        names = []
        for url in film_urls:
            if url in self.film_cache:
                names.append(self.film_cache[url])
            else:
                data = await self.fetch(url)
                if data and 'result' in data:
                    title = data['result']['properties'].get('title', 'unknown')
                    self.film_cache[url] = title
                    names.append(title)
                else:
                    names.append("unknown")
        result = ", ".join(names)
        logger.debug(f"🎬 Films: {result}")
        return result

    async def get_species_names(self, species_urls: List[str]) -> str:
        """Получаем НАЗВАНИЯ видов через запятую"""
        if not species_urls:
            return ""
        
        names = []
        for url in species_urls:
            if url in self.species_cache:
                names.append(self.species_cache[url])
            else:
                data = await self.fetch(url)
                if data and 'result' in data:
                    name = data['result']['properties'].get('name', 'unknown')
                    self.species_cache[url] = name
                    names.append(name)
                else:
                    names.append("unknown")
        return ", ".join(names)

    async def get_ship_names(self, ship_urls: List[str], ship_type: str) -> str:
        """Получаем НАЗВАНИЯ кораблей/транспорта через запятую"""
        if not ship_urls:
            return ""
        
        cache = self.ship_cache
        names = []
        for url in ship_urls:
            if url in cache:
                names.append(cache[url])
            else:
                data = await self.fetch(url)
                if data and 'result' in data:
                    name = data['result']['properties'].get('name', 'unknown')
                    cache[url] = name
                    names.append(name)
                else:
                    names.append("unknown")
        return ", ".join(names)

    async def enrich_character(self, raw_data: Dict, char_id: int) -> Dict:
        """Обогащаем персонажа - загружаем связанные данные"""
        props = raw_data.get('result', {}).get('properties', {})
        
        # Ключевой момент: homeworld - НАЗВАНИЕ, а не URL!
        homeworld_name = await self.get_planet_name(props.get('homeworld', ''))
        
        # Преобразуем списки URL в строки с названиями
        films_str = await self.get_film_names(props.get('films', []))
        species_str = await self.get_species_names(props.get('species', []))
        starships_str = await self.get_ship_names(props.get('starships', []), 'starship')
        vehicles_str = await self.get_ship_names(props.get('vehicles', []), 'vehicle')
        
        # Конвертация массы
        mass_raw = props.get('mass', '')
        mass_val = None
        if mass_raw and mass_raw != 'unknown':
            try:
                mass_val = float(mass_raw)
            except ValueError:
                pass
        
        # Конвертация роста
        height_raw = props.get('height', '')
        height_val = None
        if height_raw and height_raw != 'unknown':
            try:
                height_val = float(height_raw)
            except ValueError:
                pass
        
        return {
            'character_id': char_id,
            'name': props.get('name', 'Unknown'),
            'birth_year': props.get('birth_year', ''),
            'eye_color': props.get('eye_color', ''),
            'gender': props.get('gender', ''),
            'hair_color': props.get('hair_color', ''),
            'homeworld': homeworld_name,  # ✅ Название, не URL!
            'mass': mass_val,
            'skin_color': props.get('skin_color', ''),
            'height': height_val,
            'films': films_str,           # ✅ Строка с названиями
            'species': species_str,       # ✅ Строка с названиями
            'starships': starships_str,   # ✅ Строка с названиями
            'vehicles': vehicles_str,     # ✅ Строка с названиями
            'api_url': props.get('url', '')
        }

    async def get_total_count(self) -> int:
        data = await self.fetch(f"{self.BASE_URL}/people")
        if data:
            return data.get('total_records', 83)
        return 83

    async def load_all(self) -> List[Dict]:
        """Загрузка всех персонажей"""
        total = await self.get_total_count()
        logger.info(f"📊 Total characters to fetch: {total}")
        
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def load_one(char_id: int):
            async with semaphore:
                logger.info(f"🔄 Fetching character {char_id}/{total}")
                data = await self.fetch(f"{self.BASE_URL}/people/{char_id}")
                if data:
                    return await self.enrich_character(data, char_id)
                return None
        
        tasks = [load_one(i) for i in range(1, total + 1)]
        results = await asyncio.gather(*tasks)
        
        characters = [c for c in results if c is not None]
        logger.info(f"✅ Fetched {len(characters)} characters")
        return characters


async def main():
    logger.info("🚀 Star Wars Data Loader Started")
    
    db = Database()
    
    try:
        async with StarWarsLoader(max_concurrent=10) as loader:
            characters = await loader.load_all()
            
            saved = 0
            for char in characters:
                if await db.save_character(char):
                    saved += 1
            
            await db.get_stats()
            logger.info(f"✨ Saved {saved} new characters")
            
            # ПРОВЕРКА: выводим первые 3 записи
            logger.info("\n" + "="*60)
            logger.info("📝 SAMPLE OF SAVED DATA:")
            logger.info("="*60)
            
            all_chars = await db.get_all()
            for i, row in enumerate(all_chars[:3]):
                logger.info(f"\n--- Character {i+1} ---")
                logger.info(f"  ID: {row[1]}")
                logger.info(f"  Name: {row[2]}")
                logger.info(f"  Homeworld: {row[7]}")  # Должно быть название!
                logger.info(f"  Films: {row[11]}")      # Должны быть названия!
                logger.info(f"  Species: {row[12]}")
                logger.info(f"  Starships: {row[13]}")
                logger.info(f"  Vehicles: {row[14]}")
                
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
