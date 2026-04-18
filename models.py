from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Character(Base):
    """Модель персонажа - схема БД"""
    __tablename__ = 'characters'

    id = Column(Integer, primary_key=True, autoincrement=True)
    character_id = Column(Integer, unique=True, nullable=False, index=True)
    
    # ОСНОВНЫЕ ПОЛЯ (из задания)
    name = Column(String(200), nullable=False)
    birth_year = Column(String(50))
    eye_color = Column(String(50))
    gender = Column(String(50))
    hair_color = Column(String(50))
    homeworld = Column(String(200))  # НАЗВАНИЕ планеты!
    mass = Column(Float)
    skin_color = Column(String(50))
    height = Column(Float)
    
    # СВЯЗАННЫЕ СПИСКИ (строки через запятую)
    films = Column(Text)
    species = Column(Text)
    starships = Column(Text)
    vehicles = Column(Text)
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    api_url = Column(String(500))

    def __repr__(self):
        return f"<Character(id={self.character_id}, name='{self.name}', homeworld='{self.homeworld}')>"
