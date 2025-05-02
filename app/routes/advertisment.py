import os
import uuid

from flask import Blueprint, request, redirect, render_template, url_for, session, flash, current_app
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

@advertisement_bp.route('/ad/<int:ad_id>/edit')
def edit_ad(ad_id):
    return f"Редактирование объявления с ID {ad_id} (в разработке)"