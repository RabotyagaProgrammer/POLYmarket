
from flask import Blueprint, request, redirect, url_for, render_template,current_app
from test_db import get_user_data  # Импорт функции из твоего модуля
from jwt import ExpiredSignatureError, InvalidTokenError
import jwt
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():

    token = request.cookies.get('access_token')
    if not token:
        return redirect(url_for('auth.login'))

    try:
        payload = jwt.decode(token, 'your_secret_key', algorithms=['HS256'])
        user_id = payload.get('user_id')

        user = get_user_data(user_id)
        if not user:
            raise ValueError("Пользователь не найден")

        return render_template('index.html', username=user['username'])

    except (ExpiredSignatureError, InvalidTokenError, ValueError) as e:
        print("Ошибка JWT:", e)
        return redirect(url_for('auth.login'))

@main_bp.route('/profile')
def profile():
    return "<h2>Страница профиля (заглушка)</h2>"

@main_bp.route('/category/<category_name>')
def category(category_name):
    return f"<h2>Категория: {category_name.capitalize()} (заглушка)</h2>"
