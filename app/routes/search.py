import hashlib

import jwt
from flask import Blueprint, request, render_template, redirect, url_for

from jwt import ExpiredSignatureError, InvalidTokenError

from app.database import User
from app.jwt_utils import refresh_access_token
from test_db import get_all_advertisements_search, get_user_data

search_bp = Blueprint('search', __name__)

@search_bp.route('/search')
def search():
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
                refresh_access_token(user_id, refresh_token)
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
        category = request.args.get('category', '').strip()
        print(f"Полученная категория: {category}")  # Отладка
        # Очистка и нормализация входных параметров
        query = request.args.get('q', '').strip()
        category = request.args.get('category', '').strip()
        min_price = request.args.get('min_price', '').strip()
        max_price = request.args.get('max_price', '').strip()

        # Преобразуем пустые строки в None
        query = query if query else None
        category = category if category else None
        min_price = min_price if min_price else None
        max_price = max_price if max_price else None

        advertisements = get_all_advertisements_search(
            query=query,
            category=category,
            min_price=min_price,
            max_price=max_price
        )

        all_categories = [
            'Техника',
            'Продукты',
            'Одежда',
            'Книги',
            'Хозтовары'
        ]

        return render_template(
            'search.html',
            is_admin=user_data['is_admin'],
            advertisements=advertisements,
            query=query or '',
            category=category or '',
            min_price=min_price or '',
            max_price=max_price or '',
            all_categories=all_categories
        )
    except (ExpiredSignatureError, InvalidTokenError, ValueError) as e:
        print("Ошибка JWT:", e)
        return redirect(url_for('auth.login'))
