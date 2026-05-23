from database import engine       # Импортируем движок подключения к БД
from models import Base           # Импортируем Base с зарегистрированными моделями (Like)
# Важно: models нужно импортировать ДО create_all, иначе SQLAlchemy не знает о таблицах

Base.metadata.create_all(bind=engine)  # Создаём все таблицы в БД (если их ещё нет)
print("Таблицы созданы!")              # Подтверждение в консоль