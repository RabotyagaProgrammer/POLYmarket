import hashlib
from app.database import db, User, Advertisement
import jwt


# Добавление тестовых данных
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


def delete_user(user_id):
    """
    Удаляет пользователя по ID.

    :param user_id: ID пользователя.
    :return: True, если пользователь удалён, иначе False.
    """
    user = User.query.get(user_id)
    if not user:
        return False

    db.session.delete(user)
    db.session.commit()
    return True


def delete_all_users():
    """
    Удаляет всех пользователей из базы данных.

    :return: Количество удалённых пользователей.
    """
    count = User.query.delete()  # Удаляем все записи из таблицы User
    db.session.commit()  # Подтверждаем изменения
    return count


def verify_password(username, password):
    """
    Проверяет, соответствует ли введённый пароль хэшу, сохранённому в базе данных.

    :param username: Логин пользователя.
    :param password: Пароль в открытом виде.
    :return: True, если пароль верный, иначе False.
    """
    # Находим пользователя по логину
    user = User.query.filter_by(username=username).first()
    if not user:
        return False  # Пользователь не найден

    # Хэшируем введённый пароль и сравниваем с хэшем из базы данных
    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    return password_hash == user.password_hash


def verify_jwt(token, secret_key):
    """
    Проверяет JWT токен.

    :param token: JWT токен.
    :param secret_key: Секретный ключ для проверки подписи.
    :return: Payload токена, если он действителен, иначе сообщение об ошибке.
    """
    try:
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return "Токен истёк."
    except jwt.InvalidTokenError:
        return "Неверный токен."


def change_password(username, old_password, new_password):
    """
    Меняет пароль пользователя.

    :param username: Логин пользователя.
    :param old_password: Старый пароль.
    :param new_password: Новый пароль.
    :return: True, если пароль изменён, иначе False.
    """
    user = User.query.filter_by(username=username).first()
    if not user:
        return False

    if not verify_password(username, old_password):
        return False

    user.password_hash = hashlib.sha256(new_password.encode('utf-8')).hexdigest()
    db.session.commit()
    return True


def get_user_data(user_id):
    """
    Возвращает данные пользователя по ID.

    :param user_id: ID пользователя.
    :return: Словарь с данными пользователя или None, если пользователь не найден.
    """
    user = User.query.get(user_id)
    if not user:
        return None

    return {
        'id': user.id,
        'username': user.username,
        'is_admin': user.is_admin,
        'two_factor_secret': user.two_factor_secret
    }


def create_advertisement(user_id, title, description, price, images, category):
    """
    Создает новое объявление.

    :param user_id: ID пользователя, который создаёт объявление.
    :param title: Заголовок объявления.
    :param description: Описание объявления.
    :param price: Цена.
    :param images: Массив ссылок на изображения.
    :param category: Категория объявления.
    :return: Созданное объявление.
    """
    new_advertisement = Advertisement(
        title=title,
        description=description,
        price=price,
        images=images,
        category=category,
        user_id=user_id
    )

    db.session.add(new_advertisement)
    db.session.commit()

    return new_advertisement


def delete_advertisement(advertisement_id):
    """
    Удаляет объявление по ID.

    :param advertisement_id: ID объявления.
    :return: True, если объявление удалено, иначе False.
    """
    advertisement = Advertisement.query.get(advertisement_id)
    if not advertisement:
        return False

    db.session.delete(advertisement)
    db.session.commit()
    return True


def update_advertisement(advertisement_id, title=None, description=None, price=None, images=None, category=None):
    """
    Редактирует объявление.

    :param advertisement_id: ID объявления.
    :param title: Новый заголовок (опционально).
    :param description: Новое описание (опционально).
    :param price: Новая цена (опционально).
    :param images: Новый массив ссылок на изображения (опционально).
    :param category: Новая категория (опционально).
    :return: True, если объявление обновлено, иначе False.
    """
    advertisement = Advertisement.query.get(advertisement_id)
    if not advertisement:
        return False

    if title:
        advertisement.title = title
    if description:
        advertisement.description = description
    if price:
        advertisement.price = price
    if images:
        advertisement.images = images
    if category:
        advertisement.category = category

    db.session.commit()
    return True


def get_advertisement_data(advertisement_id):
    """
    Возвращает данные объявления по ID.

    :param advertisement_id: ID объявления.
    :return: Словарь с данными объявления или None, если объявление не найдено.
    """
    advertisement = Advertisement.query.get(advertisement_id)
    if not advertisement:
        return None

    return {
        'id': advertisement.id,
        'title': advertisement.title,
        'description': advertisement.description,
        'price': advertisement.price,
        'images': advertisement.images,
        'category': advertisement.category,
        'user_id': advertisement.user_id
    }

if __name__ == '__main__':
    from app import create_app
    app = create_app()

    with app.app_context():
        # Очистим базу пользователей (если нужно)
        delete_all_users()

        # Создадим двух пользователей
        try:
            user1 = create_user(
                username="maria",
                password="maria123",
                is_admin=False
            )
            user2 = create_user(
                username="admin",
                password="adminpass",
                is_admin=True
            )
            print("Пользователи созданы:")
            print(f"- {user1.username}, admin={user1.is_admin}")
            print(f"- {user2.username}, admin={user2.is_admin}")
        except ValueError as e:
            print("Ошибка:", e)
