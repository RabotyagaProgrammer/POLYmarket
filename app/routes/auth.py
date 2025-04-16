from flask import Blueprint, render_template, request, redirect, flash, url_for
from test_db import *
from mail import *
from key_gen import *
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')
        print(name)
        print(password)
        print(get_all_users(True))
        print(verify_password(name, password))
        print(get_user_data(name))
        key = generate_otp()
        send_email(name, key)

        # Проверка правильности пароля
        if verify_password(name, password):
            return redirect(url_for('auth.email_confirmation'))  # Переход на страницу подтверждения почты, если пароль правильный
        else:
            flash("Неверный логин или пароль!", "error")  # Если пароль неверный, выводим ошибку

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

        # Здесь позже будет логика создания пользователя и отправки email

        return redirect(url_for('auth.email_confirmation'))

    return render_template('register.html')




@auth_bp.route('/email-confirmation', methods=['GET'])
def email_confirmation():
    return render_template('email_confirmation.html')


@auth_bp.route('/confirm', methods=['POST'])
def confirm_email():
    code = request.form.get('code')
    # Тут можно будет проверять код
    return redirect(url_for('main.index'))  # Перенаправляем на главную

