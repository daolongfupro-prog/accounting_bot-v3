from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config import DATABASE_URL

# Создаем асинхронный движок
engine = create_async_engine(DATABASE_URL, echo=False)

# Фабрика сессий для работы с БД
AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def init_db(Base):
    """Функция для создания таблиц при запуске бота"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
