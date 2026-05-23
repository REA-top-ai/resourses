from flask import Flask, request, session, redirect, render_template_string, jsonify
# Flask — фреймворк для веб-приложения
# request — чтение входящих данных (параметры, JSON-тело)
# session — хранение данных пользователя между запросами (куки)
# redirect — перенаправление на другой URL
# render_template_string — рендер HTML прямо из строки
# jsonify — преобразование словаря в JSON-ответ

from google_auth_oauthlib.flow import Flow  # OAuth2-авторизация через Google
import requests as http_requests             # Переименовываем, чтобы не конфликтовало с flask.request
import os                                    # Работа с переменными окружения
from dotenv import load_dotenv               # Загрузка переменных из .env файла

from api import fetch_news, score_news       # Функции для получения и оценки новостей
from database import SessionLocal            # Фабрика сессий для работы с БД
from crud import save_like, get_likes, build_profile  # CRUD-операции с лайками и профилем

load_dotenv()  # Загружаем переменные из .env в os.environ

app = Flask(__name__)  # Создаём экземпляр Flask-приложения
app.secret_key = os.getenv("SECRET_KEY", "supersecret")  # Ключ для шифрования сессий; берём из .env

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # Разрешаем OAuth по HTTP (только для локальной разработки)

REDIRECT_URI = "http://127.0.0.1:3333/callback"  # Адрес, куда Google вернёт пользователя после входа
NEWS_API_KEY = os.getenv("NEWS_API_KEY")          # Ключ NewsAPI из .env
CLIENT_SECRET_FILE = "client_secret.json"          # Файл с данными OAuth-приложения от Google
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")    # Ключ Mistral из .env

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Gaming AI News</title>
<style>
body{margin:0;font-family:Arial;background:linear-gradient(135deg,#0f0f1a,#1c1c2e);color:white;}
.header{display:flex;justify-content:space-between;padding:15px 30px;background:#111827;}
.nav a{margin-right:15px;color:#60a5fa;text-decoration:none;}
.container{max-width:900px;margin:auto;padding:20px;}
.card{background:#1f2937;padding:18px;border-radius:14px;margin-bottom:15px;transition:0.2s;}
.card:hover{transform:translateY(-3px);}
.title{font-size:18px;font-weight:bold;}
.desc{color:#9ca3af;margin-top:6px;}
.actions{margin-top:12px;}
.btn{border:none;padding:8px 14px;border-radius:10px;cursor:pointer;}
.like{background:#ef4444;color:white;}
.open{background:#3b82f6;color:white;margin-left:8px;text-decoration:none;}
.score{color:#60a5fa;font-size:13px;margin-top:5px;}
a{color:#60a5fa;text-decoration:none;}
</style>
</head>
<body>
<div class="header">
  <div>🎮 Gaming AI News</div>
  <div class="nav">
    <a href="/">🔄 Refresh</a>
    <a href="/liked">❤️ My Likes</a>
  </div>
  <div>
    {% if user %}
      {{ user }} | <a href="/logout">Logout</a>
    {% else %}
      <a href="/login">Login</a>
    {% endif %}
  </div>
</div>
<div class="container">
  {% for n in news %}
  <div class="card">
    <div class="title">{{ n.title }}</div>
    <div class="desc">{{ n.description }}</div>
    {% if n.score is defined %}
    <div class="score">⭐ {{ n.score }}</div>
    {% endif %}
    <div class="actions">
      <button class="btn like" onclick='likeNews({{ n|tojson }}, this)'>❤️ Like</button>
      <a class="btn open" href="{{ n.url }}" target="_blank">🔗 Open</a>
    </div>
  </div>
  {% endfor %}
</div>
<script>
function likeNews(article, btn){
    if(btn.innerText.includes("Liked")) return;
    fetch("/like_async", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(article)
    })
    .then(res => res.json())
    .then(data => {
        if(data.status === "ok"){
            btn.innerText = "✅ Liked";
            btn.style.background = "#22c55e";
        }
    });
}
</script>
</body>
</html>
"""


LIKED_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>My Likes</title>
<style>
body{margin:0;font-family:Arial;background:linear-gradient(135deg,#0f0f1a,#1c1c2e);color:white;}
.header{display:flex;justify-content:space-between;padding:15px 30px;background:#111827;}
.container{max-width:900px;margin:auto;padding:20px;}
.card{background:#1f2937;padding:18px;border-radius:14px;margin-bottom:15px;}
.title{font-size:18px;font-weight:bold;}
.desc{color:#9ca3af;margin-top:6px;}
.btn{display:inline-block;margin-top:10px;background:#3b82f6;padding:8px 14px;border-radius:10px;color:white;text-decoration:none;}
a{color:#60a5fa;text-decoration:none;}
</style>
</head>
<body>
<div class="header">
  <div>❤️ My Likes</div>
  <div><a href="/">⬅ Back</a></div>
</div>
<div class="container">
  {% if not likes %}
  <h2>Пока нет лайков 😢</h2>
  {% endif %}
  {% for l in likes %}
  <div class="card">
    <div class="title">{{ l.title }}</div>
    <div class="desc">{{ l.description }}</div>
    <a class="btn" href="{{ l.url }}" target="_blank">🔗 Open</a>
  </div>
  {% endfor %}
</div>
</body>
</html>
"""

# ================= ROUTES =================

@app.route("/")       # Главная страница
def home():
    user = session.get("user")               # Читаем email пользователя из сессии (None если не вошёл)
    news = fetch_news(NEWS_API_KEY, "gaming") # Получаем свежие новости по теме gaming

    if user:  # Если пользователь авторизован — персонализируем ленту
        db = SessionLocal()  # Открываем сессию БД
        try:
            profile = build_profile(db, user)  # Строим профиль интересов на основе лайков
        finally:
            db.close()                          # Закрываем сессию БД в любом случае
        news = score_news(MISTRAL_API_KEY, profile, news)  # Оцениваем и сортируем новости под пользователя

    return render_template_string(HTML, news=news, user=user)  # Рендерим страницу с новостями


@app.route("/like_async", methods=["POST"])  # Маршрут для лайка — принимает только POST-запросы
def like_async():
    user = session.get("user")  # Проверяем, авторизован ли пользователь

    if not user:  # Если нет — возвращаем ошибку (лайкать без авторизации нельзя)
        return jsonify({"status": "error", "message": "Не авторизован"})

    data = request.json  # Читаем JSON из тела запроса (данные статьи)
    db = SessionLocal()  # Открываем сессию БД
    try:
        save_like(
            db,
            user,
            data.get("title"),        # Заголовок статьи из JSON
            data.get("description"),  # Описание статьи
            data.get("url")           # Ссылка на статью
        )
    finally:
        db.close()  # Закрываем сессию в любом случае

    return jsonify({"status": "ok"})  # Возвращаем успех — JS на фронте изменит кнопку на "Liked"


@app.route("/liked")  # Страница с понравившимися новостями
def liked():
    user = session.get("user")   # Читаем email из сессии
    db = SessionLocal()          # Открываем сессию БД
    try:
        likes = get_likes(db, user)  # Получаем все лайки пользователя из БД
    finally:
        db.close()  # Закрываем сессию

    return render_template_string(LIKED_HTML, likes=likes)  # Рендерим страницу с лайками


# ================= AUTH =================

@app.route("/login")  # Маршрут запуска Google OAuth
def login():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE,  # Берём данные приложения из файла Google
        scopes=[
            "openid",                                              # Базовая авторизация
            "https://www.googleapis.com/auth/userinfo.email",     # Доступ к email
            "https://www.googleapis.com/auth/userinfo.profile"    # Доступ к профилю
        ],
        redirect_uri=REDIRECT_URI  # Куда Google вернёт пользователя после входа
    )

    auth_url, state = flow.authorization_url(prompt="select_account")  # Генерируем URL для входа через Google
    session["state"] = state                      # Сохраняем state для защиты от CSRF-атак
    session["code_verifier"] = flow.code_verifier # Сохраняем verifier для PKCE-защиты OAuth

    return redirect(auth_url)  # Перенаправляем пользователя на страницу входа Google


@app.route("/callback")  # Маршрут, куда Google возвращает пользователя после входа
def callback():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile"
        ],
        state=session.get("state"),    # Проверяем state — защита от CSRF
        redirect_uri=REDIRECT_URI
    )

    flow.code_verifier = session.get("code_verifier")          # Восстанавливаем PKCE-verifier
    flow.fetch_token(authorization_response=request.url)       # Обмениваем код авторизации на токен

    credentials = flow.credentials  # Получаем токены доступа

    resp = http_requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",           # Запрашиваем данные профиля у Google
        headers={"Authorization": f"Bearer {credentials.token}"}  # Передаём токен доступа
    )

    session["user"] = resp.json()["email"]  # Сохраняем email пользователя в сессию
    return redirect("/")  # Перенаправляем на главную страницу


@app.route("/logout")  # Маршрут выхода из аккаунта
def logout():
    session.clear()   # Удаляем все данные из сессии (включая email пользователя)
    return redirect("/")  # Перенаправляем на главную


if __name__ == "__main__":
    app.run(debug=True, port=3333)  # Запускаем сервер на порту 3333 с режимом отладки