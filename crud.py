from models import Like  # Импортируем модель Like (ORM-класс таблицы likes)


def save_like(db, user_email, title, description, url):
    existing = db.query(Like).filter(  # Ищем в БД запись с таким же email и заголовком
        Like.user_email == user_email,
        Like.title == title
    ).first()  # Берём первое совпадение (или None если не найдено)

    if existing:  # Если лайк уже есть — ничего не делаем (защита от дублей)
        return

    like = Like(           # Создаём новый объект лайка
        user_email=user_email,
        title=title,
        description=description,
        url=url
    )

    db.add(like)    # Добавляем объект в сессию БД (ещё не сохранён)
    db.commit()     # Подтверждаем транзакцию — теперь запись в БД


def get_likes(db, user_email):
    if not user_email:  # Если email не передан (гость) — сразу возвращаем пустой список
        return []
    return db.query(Like).filter(
        Like.user_email == user_email          # Фильтруем только лайки этого пользователя
    ).order_by(Like.created_at.desc()).all()   # Сортируем: свежие лайки первыми; .all() — вернуть все


def build_profile(db, user_email):
    likes = get_likes(db, user_email)  # Получаем все лайки пользователя

    if not likes:  # Если лайков нет — возвращаем дефолтный профиль интересов
        return "gaming, esports, technology"

    return "\n".join(           # Собираем строку из заголовков и описаний лайкнутых статей
        f"{l.title} - {l.description}"
        for l in likes[:15]     # Берём максимум 15 последних лайков (лимит контекста)
        if l.title              # Пропускаем записи без заголовка
    )