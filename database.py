import hashlib

from flask_sqlalchemy import SQLAlchemy

# Инициализация SQLAlchemy
db = SQLAlchemy()


# Определение моделей
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    two_factor_secret = db.Column(db.String(16))  # Для двухфакторной аутентификации

    # Связь с объявлениями
    advertisements = db.relationship('Advertisement', backref='user', lazy=True)


class Advertisement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    images = db.Column(db.JSON)  # Массив ссылок на изображения
    category = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # Связь с пользователем


def create_user(username, password, is_admin=False, two_factor_secret=None):
    """
    Создает нового пользователя и сохраняет его в базу данных.

    :param username: Логин пользователя (уникальный).
    :param password: Пароль пользователя в открытом виде.
    :param is_admin: Флаг администратора (по умолчанию False).
    :param two_factor_secret: Секретный ключ для двухфакторной аутентификации (опционально).
    :return: Созданный объект User.
    """
    # Проверка, существует ли пользователь с таким username
    if User.query.filter_by(username=username).first():
        raise ValueError(f"Пользователь с логином '{username}' уже существует.")

    # Хэширование пароля с использованием SHA-256
    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

    # Создание нового пользователя
    new_user = User(
        username=username,
        password_hash=password_hash,
        is_admin=is_admin,
        two_factor_secret=two_factor_secret
    )

    # Добавление пользователя в сессию и сохранение в базу данных
    db.session.add(new_user)
    db.session.commit()

    return new_user


def get_all_users(include_password_hash=False, filter_admins=False):
    """
    Возвращает список всех пользователей из базы данных.

    :param include_password_hash: Включать хэш пароля в результат (по умолчанию False).
    :param filter_admins: Возвращать только администраторов (по умолчанию False).
    :return: Список словарей с данными пользователей.
    """
    query = User.query
    if filter_admins:
        query = query.filter_by(is_admin=True)

    users = query.all()
    users_data = []
    for user in users:
        user_data = {
            'id': user.id,
            'username': user.username,
            'is_admin': user.is_admin,
            'two_factor_secret': user.two_factor_secret
        }
        if include_password_hash:
            user_data['password_hash'] = user.password_hash
        users_data.append(user_data)
    return users_data
