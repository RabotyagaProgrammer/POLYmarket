from flask import Blueprint, request, redirect, url_for, render_template, current_app, make_response
from test_db import get_user_data  # Импорт функции из твоего модуля
from jwt import ExpiredSignatureError, InvalidTokenError
import jwt
from app.jwt_utils import *

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    # Проверяем наличие refresh_token в cookies
    refresh_token = request.cookies.get('refresh_token')
    if not refresh_token:
        print("Refresh-токен недействителен или отсутствует.")
        return redirect(url_for('auth.login'))

    # Ищем пользователя по refresh_token
    hashed_token = hashlib.sha256(refresh_token.encode()).hexdigest()
    user = User.query.filter_by(refresh_token=hashed_token).first()
    if not user:
        print("Refresh-токен недействителен или отсутствует.")
        return redirect(url_for('auth.login'))

    # Если refresh_token действителен, проверяем access_token
    token = request.cookies.get('access_token')
    if not token:
        if refresh_token:
            try:
                # Декодируем access_token
                payload = jwt.decode(refresh_token, 'your_secret_key', algorithms=['HS256'])
                user_id = payload.get('user_id')
                refresh_access_token(user_id,refresh_token)
            except (ExpiredSignatureError, InvalidTokenError, ValueError) as e:
                print("Ошибка JWT:", e)
                return redirect(url_for('auth.login'))

        print("ассес-токен недействителен или отсутствует.")
        return redirect(url_for('auth.login'))

    try:
        # Декодируем access_token
        payload = jwt.decode(token, 'your_secret_key', algorithms=['HS256'])
        user_id = payload.get('user_id')

        # Получаем данные пользователя
        user_data = get_user_data(user_id)
        if not user_data:
            raise ValueError("Пользователь не найден")

        return render_template('index.html', username=user_data['username'])

    except (ExpiredSignatureError, InvalidTokenError, ValueError) as e:
        print("Ошибка JWT:", e)
        return redirect(url_for('auth.login'))


@main_bp.route('/profile')
def profile():
    return "<h2>Страница профиля (заглушка)</h2>"
def artem_gay():
    return"<h2>АТРЕМ ГЕЙ</h2>"

@main_bp.route('/category/<category_name>')
def category(category_name):
    return f"<h2>Категория: {category_name.capitalize()} (заглушка)</h2>"
