import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# Твои ID
SUPERADMINS = [2103579364, 146156901]
ADMIN_IDS = SUPERADMINS 

# Умная обработка ссылки для базы данных
if DATABASE_URL:
    # Сначала проверяем старый формат (postgres://)
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
    # Потом проверяем формат Railway (postgresql://)
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Если ссылки нет совсем (например, локальный запуск), оставим пустую строку
else:
    DATABASE_URL = ""
