from flask import Blueprint, request, redirect, render_template, url_for, session, flash
from test_db import *
from test_db import get_user_by_field  # новая функция
from app.jwt_utils import *
from flask import make_response
from app.database import db, User
from mail import *
from key_gen import *

# Импорт генератора токенов

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')
        print(get_all_users())
        user = get_user_by_field('username', name)
        if user and verify_password(name, password):
            session['2fa_user_id'] = user.id

            # Сохраняем 2FA-код в поле two_factor_secret

            delete_two_factor_secret(user.id)
            key = generate_otp()
            send_email(name, key)
            add_two_factor_secret(user.id, key)
            db.session.commit()
            return redirect(url_for('auth.email_confirmation'))
        else:
            flash("Неверный логин или пароль")

    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')

        if password != confirm:
            flash('Пароли не совпадают')
            return redirect(url_for('auth.register'))
        delete_user(2)
        if create_user(email, name,  password, False, None, None):
            user = get_user_by_field('username', email)
            session['2fa_user_id'] = user.id
            print(name)
            id_tmp = user.id
            key = generate_otp()
            send_email(email, key)
            add_two_factor_secret(id_tmp, key)
            # Здесь позже будет логика создания пользователя и отправки email
            db.session.commit()
            return redirect(url_for('auth.email_confirmation'))
        else:
            flash('Такой пользователь уже существует')
            return redirect(url_for('auth.register'))

    return render_template('register.html')


@auth_bp.route('/email-confirmation', methods=['GET', 'POST'])
def email_confirmation():
    user_id = session.get('2fa_user_id')
    if not user_id:
        flash("Сессия истекла. Пожалуйста, войдите снова.")
        return redirect(url_for('auth.login'))

    user = User.query.get(user_id)
    print(user.two_factor_secret)
    if not user:
        flash("Пользователь не найден.")
        print("BBBBBBBBBBBBBBBBBBBBBBBBbb")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        entered_code = request.form.get('code')
        print("BBBBBBBBBBBBBBBBBBBBBBBBbb")
        print(entered_code)

        if entered_code == get_two_factor_secret(user.id):
            token = generate_token(user_id)
            refresh_token = generate_and_save_refresh_token(user_id)
            print("BBBBBBBBBBBBBBBBBBBBBBBBbb")
            session.pop('2fa_user_id', None)
            user.two_factor_secret = None  # Стираем после успешной авторизации
            db.session.commit()
            print("BBBBBBBBBBBBBBBBBBBBBBBBbb")
            response = make_response(redirect(url_for('main.index')))
            response.set_cookie('access_token', token, httponly=True, max_age=3600)
            response.set_cookie('refresh_token', refresh_token, httponly=True, max_age=36000)
            delete_two_factor_secret(user_id)
            return response
        else:
            flash("Неверный код подтверждения")

    return render_template('email_confirmation.html')


@auth_bp.route('/confirm', methods=['POST'])
def confirm_email():
    code = request.form.get('code')
    # Тут можно будет проверять код
    return redirect(url_for('main.index'))  # Перенаправляем на главную
