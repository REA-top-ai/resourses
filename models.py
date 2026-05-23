from sqlalchemy import Column, Integer, String, Text, DateTime  # Типы колонок для ORM
from datetime import datetime  # Для установки текущего времени по умолчанию
from database import Base      # Базовый класс — от него наследуют все модели


class Like(Base):              # Модель таблицы "likes" в базе данных
    __tablename__ = "likes"    # Имя таблицы в PostgreSQL

    id = Column(Integer, primary_key=True, autoincrement=True)  # Уникальный ID записи, автоинкремент
    user_email = Column(String(255), nullable=False, index=True) # Email пользователя; index ускоряет поиск
    title = Column(String(500), nullable=False)                  # Заголовок статьи; обязательное поле
    description = Column(Text)                                   # Описание статьи; может быть пустым
    url = Column(Text)                                           # Ссылка на статью; может быть пустой
    created_at = Column(DateTime, default=datetime.utcnow)       # Дата лайка; ставится автоматически

    def __repr__(self):  # Строковое представление объекта — удобно при отладке в консоли
        return f"<Like(title='{self.title}')>"