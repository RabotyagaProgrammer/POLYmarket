import hashlib
import secrets

from sqlalchemy import func, String

from app.database import db, User, Advertisement,Image

import jwt


# Добавление тестовых данных
def create_user(email, name, password, is_admin=False, two_factor_secret=None, refresh_token=None):
    """
    Создает нового пользователя и сохраняет его в базу данных.

    :param email: Логин пользователя (уникальный).
    :param name: имя фамилия отчество пользователя
    :param password: Пароль пользователя в открытом виде.
    :param is_admin: Флаг администратора (по умолчанию False).
    :param two_factor_secret: Секретный ключ для двухфакторной аутентификации (опционально).
    :param refresh_token: Рефреш токен
    :return: Созданный объект User.
    """
    # Проверка, существует ли пользователь с таким username
    if User.query.filter_by(email=email).first():
        raise ValueError(f"Пользователь с логином '{email}' уже существует.")

    # Хэширование пароля с использованием SHA-256
    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

    # Создание нового пользователя
    new_user = User(
        email=email,
        name=name,
        password_hash=password_hash,
        is_admin=is_admin,
        two_factor_secret=two_factor_secret,
        refresh_token=refresh_token
    )

    # Добавление пользователя в сессию и сохранение в базу данных
    db.session.add(new_user)
    db.session.commit()

    return new_user


def get_user_by_field(field, value):
    """
    Универсальная функция для поиска пользователя по заданному полю.
    Пример: get_user_by_field('username', 'john')
    """
    from app.database import User
    if hasattr(User, field):
        return User.query.filter(getattr(User, field) == value).first()
    else:
        raise AttributeError(f"User has no field '{field}'")


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
            'email': user.email,
            'name': user.name,
            'is_admin': user.is_admin,
            'two_factor_secret': user.two_factor_secret,
            'refresh': user.refresh_token
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
    user = User.query.filter_by(email=username).first()
    if not user:
        return False  # Пользователь не найден

    # Хэшируем введённый пароль и сравниваем с хэшем из базы данных
    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    return password_hash == user.password_hash


def change_password(username, old_password, new_password):
    """
    Меняет пароль пользователя.

    :param username: Логин пользователя.
    :param old_password: Старый пароль.
    :param new_password: Новый пароль.
    :return: True, если пароль изменён, иначе False.
    """
    user = User.query.filter_by(email=username).first()
    if not user:
        return False

    if not verify_password(username, old_password):
        return False

    user.password_hash = hashlib.sha256(new_password.encode('utf-8')).hexdigest()
    db.session.commit()
    return True
def get_all_advertisements():
    """
    Возвращает список всех объявлений.
    :return: Список словарей с данными объявлений.
    """
    ads = Advertisement.query.all()
    result = []
    for ad in ads:
        result.append({
            'id': ad.id,
            'title': ad.title,
            'description': ad.description,
            'price': ad.price,
            'images': ad.images,
            'category': ad.category,
            'user_id': ad.user_id
        })
    return result

def get_user_data(user_id):
    """
    Возвращает данные пользователя по ID, включая его объявления (вся информация об объявлениях).

    :param user_id: ID пользователя.
    :return: Словарь с данными пользователя или None, если пользователь не найден.
    """
    user = User.query.get(user_id)
    if not user:
        return None

    return {
        'id': user.id,
        'email': user.email,
        'tg_contact': user.tg_contact,
        'name': user.name,
        'is_admin': user.is_admin,
        'two_factor_secret': user.two_factor_secret,
        'refresh': user.refresh_token,
        'advertisements': [
            {
                'id': ad.id,
                'title': ad.title,
                'description': ad.description,
                'price': ad.price,
                'images': ad.images,
                'category': ad.category,
                'user_id': ad.user_id
            }
            for ad in user.advertisements
        ]
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


def add_two_factor_secret(user_id, secret):
    """
    Добавляет two_factor_secret для пользователя с указанным user_id.

    :param user_id: ID пользователя
    :param secret: Новый two_factor_secret (например, секретный ключ для TOTP)
    :return: True, если операция успешна, иначе False
    """
    # Находим пользователя по ID
    user = User.query.get(user_id)
    if not user:
        print(f"Пользователь с ID {user_id} не найден.")
        return False

    # Обновляем two_factor_secret
    user.two_factor_secret = secret
    try:
        db.session.commit()
        print(f"Two-factor secret успешно добавлен для пользователя {user.email}.")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка при добавлении two_factor_secret: {e}")
        return False


def delete_two_factor_secret(user_id):
    """
    Удаляет two_factor_secret для пользователя с указанным user_id.

    :param user_id: ID пользователя
    :return: True, если операция успешна, иначе False
    """
    # Находим пользователя по ID
    user = User.query.get(user_id)
    if not user:
        print(f"Пользователь с ID {user_id} не найден.")
        return False

    # Удаляем two_factor_secret
    user.two_factor_secret = None
    try:
        db.session.commit()
        print(f"Two-factor secret успешно удален для пользователя {user.email}.")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка при удалении two_factor_secret: {e}")
        return False


def get_two_factor_secret(user_id):
    """
    Получает two_factor_secret для пользователя с указанным user_id.

    :param user_id: ID пользователя
    :return: two_factor_secret (строка) или None, если ключ не найден
    """
    # Находим пользователя по ID
    user = User.query.get(user_id)
    if not user:
        print(f"Пользователь с ID {user_id} не найден.")
        return None

    # Проверяем наличие two_factor_secret
    if not user.two_factor_secret:
        print(f"Two-factor secret для пользователя {user.email} не установлен.")
        return None

    # Возвращаем two_factor_secret
    print(f"Two-factor secret успешно получен для пользователя {user.email}.")
    return user.two_factor_secret


def update_two_factor_secret(user_id, new_secret):
    """
    Изменяет two_factor_secret для пользователя с указанным user_id.

    :param user_id: ID пользователя
    :param new_secret: Новый two_factor_secret (например, секретный ключ для TOTP)
    :return: True, если операция успешна, иначе False
    """
    # Находим пользователя по ID
    user = User.query.get(user_id)
    if not user:
        print(f"Пользователь с ID {user_id} не найден.")
        return False

    # Проверяем наличие текущего two_factor_secret
    if not user.two_factor_secret:
        print(f"Two-factor secret для пользователя {user.email} не установлен. Используйте add_two_factor_secret.")
        return False

    # Обновляем two_factor_secret
    user.two_factor_secret = new_secret
    try:
        db.session.commit()
        print(f"Two-factor secret успешно изменен для пользователя {user.email}.")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка при изменении two_factor_secret: {e}")
        return False


def create_refresh_token(user_id):
    """
    Создает и сохраняет новый refresh-токен для пользователя.

    :param user_id: ID пользователя
    :return: Исходный refresh-токен (строка) или None, если операция не удалась
    """
    # Генерация нового refresh-токена
    refresh_token = secrets.token_urlsafe(32)

    # Хэширование refresh-токена
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


def delete_refresh_token(user_id):
    """
    Удаляет refresh-токен для пользователя.

    :param user_id: ID пользователя
    :return: True, если операция успешна, иначе False
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


def get_refresh_token(user_id):
    """
    Получает хэшированный refresh-токен для пользователя.

    :param user_id: ID пользователя
    :return: Хэшированный refresh-токен (строка) или None, если токен не найден
    """
    # Находим пользователя по ID
    user = User.query.get(user_id)
    if not user:
        print(f"Пользователь с ID {user_id} не найден.")
        return None

    # Проверяем наличие refresh-токена
    if not user.refresh_token:
        print(f"Refresh-токен для пользователя {user.email} не установлен.")
        return None

    print(f"Refresh-токен успешно получен для пользователя {user.email}.")
    return user.refresh_token


def verify_refresh_token(user_id, provided_token):
    """
    Проверяет, является ли предоставленный refresh-токен действительным.

    :param user_id: ID пользователя
    :param provided_token: Исходный refresh-токен, предоставленный клиентом
    :return: True, если токен верный, иначе False
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
def search_advertisements(field_name, value):
    # Проверяем, существует ли такое поле в модели Advertisement
    valid_fields = [col.key for col in Advertisement.__table__.columns] + ['images.url']

    if field_name not in valid_fields:
        raise ValueError(f"Field '{field_name}' is not a valid column in Advertisement")

    # Формируем фильтр поиска
    if field_name == 'images.url':
        # Поиск по URL изображения через связь с Image
        query = Advertisement.query.join(Advertisement.images).filter(Image.url.ilike(f"%{value}%"))
    else:
        # Обычный поиск по полю Advertisement
        column = getattr(Advertisement, field_name)
        if isinstance(column.type, String):
            # Для строковых полей — нечеткое совпадение
            query = Advertisement.query.filter(column.ilike(f"%{value}%"))
        else:
            # Для других типов — точное совпадение
            try:
                # Пробуем привести значение к типу колонки
                typed_value = column.type.python_type(value)
                query = Advertisement.query.filter(column == typed_value)
            except (ValueError, TypeError):
                raise ValueError(f"Value '{value}' can't be cast to type {column.type.python_type}")

    return query.all()


CATEGORY_MAP = {
    'техника': 'tech',
    'продукты': 'food',
    'одежда': 'clothes',
    'книги': 'books',
    'хозтовары': 'home'
}


def get_all_advertisements_search(query=None, category=None, min_price=None, max_price=None):
    filters = []

    print("🔍 Поиск объявлений с параметрами:", flush=True)

    if query:
        lower_query = query.lower()
        print(f"- Поиск по заголовку: '{query}' (в нижнем регистре)", flush=True)
        filters.append(func.lower(Advertisement.title).like(f"%{lower_query}%"))

    # Всегда выводим все категории
    all_categories = (
        db.session.query(Advertisement.category)
        .distinct()
        .order_by(Advertisement.category)
        .all()
    )
    category_list = [c[0] for c in all_categories]
    print(f"📚 Все доступные категории в базе: {category_list}", flush=True)

    if category:
        category_lower = category.lower()
        translated_slug = CATEGORY_MAP.get(category_lower)
        if translated_slug:
            print(f"- Фильтр по категории: '{category}' → slug: '{translated_slug}'", flush=True)
            filters.append(func.lower(Advertisement.category) == translated_slug.lower())
        else:
            print(f"⚠️ Неизвестная категория: '{category}'", flush=True)

    if min_price:
        try:
            min_price_float = float(min_price)
            filters.append(Advertisement.price >= min_price_float)
            print(f"- Минимальная цена: {min_price_float}", flush=True)
        except ValueError:
            print(f"⚠️ Ошибка: min_price '{min_price}' не является числом", flush=True)

    if max_price:
        try:
            max_price_float = float(max_price)
            filters.append(Advertisement.price <= max_price_float)
            print(f"- Максимальная цена: {max_price_float}", flush=True)
        except ValueError:
            print(f"⚠️ Ошибка: max_price '{max_price}' не является числом", flush=True)

    # Собираем и выводим результаты
    results = Advertisement.query.filter(*filters).all()
    print(f"🎯 Найдено объявлений: {len(results)}", flush=True)
    for ad in results:
        print(
            f"   • ID={ad.id}, title='{ad.title}', price={ad.price}, category='{ad.category}'",
            flush=True
        )

    return results