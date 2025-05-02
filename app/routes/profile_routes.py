from flask import Blueprint, request, render_template, redirect, url_for
from app.database import db, User
from test_db import get_user_data, change_password
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile')
def profile():
    token = request.cookies.get('access_token')
    if not token:
        return redirect(url_for('auth.login'))
    try:
        payload = jwt.decode(token, 'your_secret_key', algorithms=['HS256'])
        user_id = payload['user_id']
        user_data = get_user_data(user_id)
        return render_template('profile.html', user=user_data)
    except (ExpiredSignatureError, InvalidTokenError, ValueError):
        return redirect(url_for('auth.login'))

@profile_bp.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    token = request.cookies.get('access_token')
    if not token:
        return redirect(url_for('auth.login'))

    try:
        payload = jwt.decode(token, 'your_secret_key', algorithms=['HS256'])
        user_id = payload['user_id']
        user = User.query.get(user_id)
    except Exception:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        user.name = request.form.get('name')
        user.email = request.form.get('email')
        user.tg_contact = request.form.get('tg_contact')
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')

        if old_password and new_password:
            if not change_password(user.email, old_password, new_password):
                return render_template('edit_profile.html', user=user, error="Старый пароль неверный")

        try:
            db.session.commit()
            return redirect(url_for('profile.profile'))
        except Exception:
            db.session.rollback()
            return render_template('edit_profile.html', user=user, error="Ошибка при сохранении")

    return render_template('edit_profile.html', user=user)
