from flask import Blueprint, request, redirect, url_for, render_template, current_app, make_response
from test_db import get_user_data, change_password  # Импорт функции из твоего модуля
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

        return render_template('index.html', username=user_data['email'])

    except (ExpiredSignatureError, InvalidTokenError, ValueError) as e:
        print("Ошибка JWT:", e)
        return redirect(url_for('auth.login'))


@main_bp.route('/profile')
def profile():
    access_token = request.cookies.get('access_token')
    refresh_token = request.cookies.get('refresh_token')

    if not access_token:
        return redirect(url_for('auth.login'))

    try:
        payload = jwt.decode(access_token, 'your_secret_key', algorithms=['HS256'])
        user_id = payload.get('user_id')

        user_data = get_user_data(user_id)
        print(user_data['tg_contact'])
        if not user_data:
            return redirect(url_for('auth.login'))

        return render_template('profile.html', user=user_data)

    except (ExpiredSignatureError, InvalidTokenError, ValueError):
        return redirect(url_for('auth.login'))

@main_bp.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    token = request.cookies.get('access_token')
    if not token:
        return redirect(url_for('auth.login'))

    try:
        payload = jwt.decode(token, 'your_secret_key', algorithms=['HS256'])
        user_id = payload.get('user_id')
        user = User.query.get(user_id)
        if not user:
            return redirect(url_for('auth.login'))
    except Exception:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        tg_contact = request.form.get('tg_contact')
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')

        # Обновляем имя, email, Telegram
        user.name = name
        user.email = email
        user.tg_contact = tg_contact
        print(tg_contact)

        # Смена пароля, если указаны оба
        if old_password and new_password:
            if not change_password(user.email, old_password, new_password):
                return render_template('edit_profile.html', user=user, error="Старый пароль неверный")

        try:
            db.session.commit()
            db.session.refresh(user)

            return redirect(url_for('main.profile'))
        except Exception as e:
            db.session.rollback()
            return render_template('edit_profile.html', user=user, error="Ошибка при сохранении данных")

    return render_template('edit_profile.html', user=user)

@main_bp.route('/ad/<int:ad_id>')
def view_ad(ad_id):
    ad = Advertisement.query.get_or_404(ad_id)
    return f"Это заглушка для объявления: {ad.title}"

@main_bp.route('/category/<category_name>')
def category(category_name):
    return f"<h2>Категория: {category_name.capitalize()} (заглушка)</h2>"
