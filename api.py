import requests  # Библиотека для HTTP-запросов
import random    # Библиотека для случайных чисел и перемешивания

BASE_URL = "https://newsapi.org/v2"                          # Базовый адрес NewsAPI
MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"  # Адрес Mistral для генерации текста


def fetch_news(api_key: str, topic: str):
    page = random.randint(1, 5)  # Случайная страница (1–5) — чтобы каждый раз были разные новости

    r = requests.get(
        f"{BASE_URL}/everything",  # Эндпоинт NewsAPI — поиск по всем источникам
        params={
            "q": topic,             # Поисковый запрос (например, "gaming")
            "language": "en",       # Только англоязычные статьи
            "pageSize": 10,         # Вернуть 10 статей
            "sortBy": "publishedAt", # Сортировка: свежие первыми
            "page": page,           # Случайная страница — добавляет разнообразие
            "apiKey": api_key       # Ключ авторизации NewsAPI
        }
    )

    r.raise_for_status()  # Если сервер вернул ошибку (4xx/5xx) — выбросить исключение

    articles = r.json().get("articles", [])  # Извлекаем список статей; если нет — пустой список
    random.shuffle(articles)                 # Перемешиваем статьи случайно — каждый раз разный порядок

    return articles  # Возвращаем перемешанный список статей


def score_news(mistral_key: str, user_profile: str, articles: list):
    scored = []  # Список, куда будем складывать статьи с оценками

    for a in articles:  # Перебираем каждую статью
        prompt = f"""
Оцени насколько пользователю понравится новость от 0 до 10.

Профиль пользователя:
{user_profile}  # Вставляем интересы пользователя (построены на основе его лайков)

Новость:
{a.get('title')}        # Заголовок статьи
{a.get('description')}  # Описание статьи

Ответ ТОЛЬКО число.  # Ограничиваем ответ — чтобы проще парсить
"""

        try:
            r = requests.post(
                MISTRAL_URL,  # Отправляем запрос к Mistral
                headers={
                    "Authorization": f"Bearer {mistral_key}",  # Авторизация
                    "Content-Type": "application/json"          # Формат тела запроса
                },
                json={
                    "model": "mistral-small-latest",  # Лёгкая и быстрая модель
                    "messages": [{"role": "user", "content": prompt}],  # Промпт как сообщение
                    "temperature": 0  # Температура 0 — максимально точный, детерминированный ответ
                },
                timeout=10  # Ждём ответа не более 10 секунд
            )

            text = r.json()["choices"][0]["message"]["content"]  # Извлекаем текст ответа от модели
            # Оставляем только цифры и точку, затем конвертируем в float (например, "8.5" → 8.5)
            score = float("".join(c for c in text if c.isdigit() or c == "."))

        except Exception:
            score = 5.0  # Если что-то пошло не так — ставим нейтральную оценку 5.0

        a["score"] = score   # Добавляем оценку прямо в словарь статьи
        scored.append(a)     # Добавляем оценённую статью в список

    # Сортируем статьи по оценке от большей к меньшей и возвращаем
    return sorted(scored, key=lambda x: x.get("score", 0), reverse=True)