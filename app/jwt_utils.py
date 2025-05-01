import jwt
from datetime import datetime, timedelta
import secrets
import hashlib

from app.database import db, User, Advertisement

SECRET_KEY = 'your_secret_key'
REFRESH_SECRET_KEY = 'your_refresh_secret_key'


def generate_token(user_id):
    """
    Генерирует новый access token.
    """
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=1)  # Access token действителен 1 час
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')


def generate_and_save_refresh_token(user_id):
    """
    Генерирует и сохраняет refresh token для пользователя.
    """
    # Создаем refresh token
    refresh_token = secrets.token_urlsafe(32)

    # Хэшируем refresh token
    hashed_token = hashlib.sha256(refresh_token.encode()).hexdigest()

    # Находим пользователя по ID
    user = User.query.get(user_id)
    if not user:
        print(f"Пользователь с ID {user_id} не найден.")
        return None

    # Сохраняем хэш в базу данных
    user.refresh_token = hashed_token
    try:
        db.session.commit()
        print(f"Refresh-токен успешно создан для пользователя {user.email}.")
        return refresh_token  # Возвращаем исходный токен для клиента
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка при создании refresh-токена: {e}")
        return None


def verify_refresh_token(user_id, provided_token):
    """
    Проверяет, является ли предоставленный refresh-токен действительным.
    """
    # Находим пользователя по ID
    user = User.query.get(user_id)
    if not user:
        print(f"Пользователь с ID {user_id} не найден.")
        return False

    # Проверяем наличие refresh-токена
    if not user.refresh_token:
        print(f"Refresh-токен для пользователя {user.email} не установлен.")
        return False

    # Хэшируем предоставленный токен
    hashed_provided_token = hashlib.sha256(provided_token.encode()).hexdigest()

    # Сравниваем хэши
    if user.refresh_token == hashed_provided_token:
        print(f"Refresh-токен для пользователя {user.email} верный.")
        return True
    else:
        print(f"Refresh-токен для пользователя {user.email} неверный.")
        return False


def refresh_access_token(user_id, provided_refresh_token):
    """
    Обновляет access token с использованием refresh token.
    """
    # Проверяем refresh token
    if not verify_refresh_token(user_id, provided_refresh_token):
        print("Refresh token недействителен.")
        return None

    # Генерируем новый access token
    new_access_token = generate_token(user_id)
    return new_access_token


def delete_refresh_token(user_id):
    """
    Удаляет refresh-токен для пользователя.
    """
    # Находим пользователя по ID
    user = User.query.get(user_id)
    if not user:
        print(f"Пользователь с ID {user_id} не найден.")
        return False

    # Удаляем refresh-токен
    user.refresh_token = None
    try:
        db.session.commit()
        print(f"Refresh-токен успешно удален для пользователя {user.email}.")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка при удалении refresh-токена: {e}")
        return False
