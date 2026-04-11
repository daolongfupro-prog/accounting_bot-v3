from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=True) # Появится после перехода по ссылке
    full_name = Column(String, nullable=False)
    role = Column(String, default="client") # 'superadmin', 'admin', 'client'
    language = Column(String, default="ru") # 'ru', 'uz', 'en'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи с другими таблицами
    packages = relationship("Package", back_populates="user")

class Package(Base):
    """Пакеты массажа или курсы обучения"""
    __tablename__ = 'packages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    package_type = Column(String, nullable=False) # 'massage' или 'education'
    total_sessions = Column(Integer, nullable=False) 
    used_sessions = Column(Integer, default=0)
    status = Column(String, default="active") # 'active' или 'completed'
    edu_level = Column(Integer, default=1) # 1, 2, 3 (для курсов обучения)
    payment_date = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="packages")
