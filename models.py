from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Character(Base):
    """Модель персонажа Star Wars для базы данных"""
    __tablename__ = 'characters'

    id = Column(Integer, primary_key=True, autoincrement=True)
    character_id = Column(Integer, unique=True, nullable=False, index=True)  # uid из API
    name = Column(String(200), nullable=False)
    birth_year = Column(String(50))
    eye_color = Column(String(50))
    gender = Column(String(50))
    hair_color = Column(String(50))
    homeworld = Column(String(500))
    mass = Column(Float)  # вес в кг
    skin_color = Column(String(50))
    height = Column(Float)  # рост в см
    created_at = Column(DateTime, default=datetime.utcnow)
    api_created = Column(String(100))
    api_edited = Column(String(100))

    def to_dict(self):
        """Преобразует объект в словарь"""
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
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
