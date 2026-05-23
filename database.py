from sqlalchemy import create_engine             # Создание движка подключения к БД
from sqlalchemy.orm import declarative_base, sessionmaker  # Base — базовый класс моделей; sessionmaker — фабрика сессий
import os                                        # Работа с переменными окружения
from dotenv import load_dotenv                   # Загрузка переменных из .env

load_dotenv()  # Читаем .env файл и загружаем переменные в окружение

DATABASE_URL = os.getenv("DATABASE_URL")  # Строка подключения к БД (например, postgresql://user:pass@host/db)

if not DATABASE_URL:  # Если переменная не задана — сразу падаем с понятной ошибкой
    raise ValueError("DATABASE_URL не задан в .env файле!")

engine = create_engine(DATABASE_URL)        # Создаём движок SQLAlchemy — управляет подключением к БД
SessionLocal = sessionmaker(bind=engine)    # Фабрика сессий — каждый вызов SessionLocal() даёт новую сессию
Base = declarative_base()                   # Базовый класс для всех ORM-моделей (от него наследует Like)