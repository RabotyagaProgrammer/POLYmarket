import hashlib
from flask_sqlalchemy import SQLAlchemy

# Инициализация SQLAlchemy
db = SQLAlchemy()


# Определение моделей
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), unique=True, nullable=False)
    tg_contact = db.Column(db.String(80), unique=False, nullable=True)
    name = db.Column(db.String(80), unique=False, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    two_factor_secret = db.Column(db.String(16))  # Для двухфакторной аутентификации
    refresh_token = db.Column(db.String(256), nullable=True)  # Хэшированный refresh-токен
    # Связь с объявлениями
    advertisements = db.relationship('Advertisement', backref='user', lazy=True)


class Advertisement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    #images = db.Column(db.JSON)  # Массив ссылок на изображения
    category = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # Связь с пользователем
    images = db.relationship('Image', backref='advertisement', lazy=True, cascade="all, delete-orphan")


class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    advertisement_id = db.Column(db.Integer, db.ForeignKey('advertisement.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)  # Имя файла на диске
    url_path = db.Column(db.String(500), nullable=False)  # Полный путь для <img src="">
    is_main = db.Column(db.Boolean, default=False)  # Основное изображение объявления