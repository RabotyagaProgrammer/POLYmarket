import os
import uuid

from flask import Blueprint, request, redirect, render_template, url_for, session, flash, current_app
from jwt import ExpiredSignatureError, InvalidTokenError

from test_db import *
from test_db import get_user_by_field  # новая функция
from app.jwt_utils import *
from flask import make_response
from app.database import db, User, Image
from mail import *
from key_gen import *

# Импорт генератора токенов

advertisement_bp = Blueprint('advert', __name__)



@advertisement_bp.route('/ad/<int:ad_id>')
def ad_detail(ad_id):
    # Получаем объявление из БД
    ad_data = get_advertisement_data(ad_id)
    if not ad_data:
        return "Объявление не найдено", 404

    # Получаем данные пользователя-владельца
    user_data = get_user_data(ad_data['user_id'])
    if not user_data:
        return "Владелец объявления не найден", 404

    # Передаём всё в шаблон
    return render_template('ad_detail.html', ad=ad_data, owner=user_data)


@advertisement_bp.route('/newAdvertisement', methods=['GET', 'POST'])
def new_advertisement():
    token = request.cookies.get('access_token')
    if not token:
        flash("Вы не авторизованы.")
        return redirect(url_for('auth.login'))

    try:
        payload = jwt.decode(token, 'your_secret_key', algorithms=['HS256'])
        user_id = payload.get('user_id')
        if not user_id:
            raise ValueError("Неверный токен")
    except jwt.ExpiredSignatureError:
        flash("Сессия истекла.")
        return redirect(url_for('auth.login'))
    except jwt.InvalidTokenError:
        flash("Неверный токен.")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        price = float(request.form['price'])
        category = request.form['category']

        # Создаем объявление
        new_ad = Advertisement(
            title=title,
            description=description,
            price=price,
            category=category,
            user_id=user_id
        )
        db.session.add(new_ad)
        db.session.commit()  # Чтобы получить ID нового объявления

        # Обработка изображений
        image_files = request.files.getlist('images')
        upload_folder = os.path.join(current_app.root_path, 'static', 'images')

        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        for file in image_files:
            if file.filename:
                ext = os.path.splitext(file.filename)[1]  # Получаем расширение
                unique_filename = f"{uuid.uuid4()}{ext}"
                file.save(os.path.join(upload_folder, unique_filename))

                image_url = f'/static/images/{unique_filename}'

                new_image = Image(
                    advertisement_id=new_ad.id,
                    filename=unique_filename,
                    url_path=image_url,
                    is_main=len(new_ad.images) == 0  # Первое фото — основное
                )
                db.session.add(new_image)

        db.session.commit()
        flash("Объявление успешно создано!")
        return redirect(url_for('main.index'))

    return render_template('new_advertisement.html')

@advertisement_bp.route('/category/<category_name>')
def category(category_name):
    return f"<h2>Категория: {category_name.capitalize()} (заглушка)</h2>"

@advertisement_bp.route('/ad/<int:ad_id>/delete', methods=['POST'])
def delete_ad(ad_id):
    ad = Advertisement.query.get_or_404(ad_id)
    db.session.delete(ad)
    db.session.commit()
    flash('Объявление удалено')
    return redirect(url_for('profile.profile'))

@advertisement_bp.route('/ad/<int:ad_id>/edit', methods=['GET', 'POST'])
def edit_ad(ad_id):
    # Проверка авторизации пользователя
    token = request.cookies.get('access_token')
    if not token:
        return redirect(url_for('auth.login'))

    try:
        payload = jwt.decode(token, 'your_secret_key', algorithms=['HS256'])
        user_id = payload['user_id']
    except (ExpiredSignatureError, InvalidTokenError, ValueError):
        return redirect(url_for('auth.login'))

    # Получаем объявление и проверяем, принадлежит ли оно пользователю
    ad = Advertisement.query.get_or_404(ad_id)
    if ad.user_id != user_id:
        return "Доступ запрещён", 403

    if request.method == 'POST':
        # Обновляем основные поля объявления
        ad.title = request.form['title']
        ad.description = request.form['description']
        ad.price = float(request.form['price'])  # Преобразуем цену в число
        ad.category = request.form['category']

        # Обработка новых изображений
        files = request.files.getlist('images')  # Получаем список загруженных файлов
        upload_folder = os.path.join(current_app.root_path, 'static', 'images')

        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        for file in files:
            if file and file.filename:  # Проверяем, что файл существует
                ext = os.path.splitext(file.filename)[1]  # Получаем расширение файла
                unique_filename = f"{uuid.uuid4()}{ext}"  # Генерируем уникальное имя
                file.save(os.path.join(upload_folder, unique_filename))  # Сохраняем файл

                image_url = f'/static/images/{unique_filename}'  # URL для доступа к файлу

                # Создаем новый объект Image и связываем его с объявлением
                new_image = Image(
                    advertisement_id=ad.id,
                    filename=unique_filename,
                    url_path=image_url,
                    is_main=len(ad.images) == 0  # Первое фото делаем основным
                )
                db.session.add(new_image)

        db.session.commit()
        flash("Объявление успешно обновлено.", "success")
        return redirect(url_for('profile.profile'))

    # Если метод GET, отображаем форму редактирования
    return render_template('edit_ad.html', ad=ad)

@advertisement_bp.route('/delete_image/<int:image_id>', methods=['POST'])
def delete_image(image_id):
    # Получаем токен
    token = request.cookies.get('access_token')
    if not token:
        flash("Авторизуйтесь, чтобы продолжить.", "warning")
        return redirect(url_for('auth.login'))

    try:
        payload = jwt.decode(token, 'your_secret_key', algorithms=['HS256'])
        user_id = payload['user_id']
    except (ExpiredSignatureError, InvalidTokenError, ValueError):
        flash("Недействительный токен. Пожалуйста, войдите снова.", "danger")
        return redirect(url_for('auth.login'))

    # Получаем изображение и проверяем владельца объявления
    image = Image.query.get_or_404(image_id)
    ad = image.advertisement

    if ad.user_id != user_id:
        flash("Нет доступа.", "danger")
        return redirect(url_for('profile.profile'))

    db.session.delete(image)
    db.session.commit()
    flash("Изображение удалено.", "success")
    return redirect(url_for('advert.edit_ad', ad_id=ad.id))