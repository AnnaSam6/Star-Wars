from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Character(Base):
    """Модель персонажа Star Wars с ВСЕМИ обязательными полями"""
    __tablename__ = 'characters'

    id = Column(Integer, primary_key=True, autoincrement=True)
    character_id = Column(Integer, unique=True, nullable=False, index=True)
    
    # Основные поля из задания
    name = Column(String(200), nullable=False)
    birth_year = Column(String(50))
    eye_color = Column(String(50))
    gender = Column(String(50))
    hair_color = Column(String(50))
    homeworld = Column(String(200))  # НАЗВАНИЕ планеты, не URL!
    mass = Column(Float)
    skin_color = Column(String(50))
    height = Column(Float)
    
    # Дополнительные поля (связанные списки)
    films = Column(Text)  # список фильмов через запятую
    species = Column(Text)  # список видов через запятую
    starships = Column(Text)  # список кораблей через запятую
    vehicles = Column(Text)  # список транспорта через запятую
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    url = Column(String(500))

    def to_dict(self):
        return {
            'id': self.id,
            'character_id': self.character_id,
            'name': self.name,
            'birth_year': self.birth_year,
            'eye_color': self.eye_color,
            'gender': self.gender,
            'hair_color': self.hair_color,
            'homeworld': self.homeworld,
            'mass': self.mass,
            'skin_color': self.skin_color,
            'height': self.height,
            'films': self.films,
            'species': self.species,
            'starships': self.starships,
            'vehicles': self.vehicles
        }
