from flask_restx import Api, Resource, fields
from flask import Blueprint, request
from test_db import *
from app.jwt_utils import generate_token
from mail import send_email


api_bp = Blueprint('api', __name__)
api = Api(api_bp, version='1.0', title='User. API',
          description='API для работы с пользователями и обьявлениями')

create_advertisement_model = api.model('CreateAdvertisement', {
    'user_id': fields.Integer(required=True, description='ID пользователя, который создает объявление'),
    'title': fields.String(required=True, description='Заголовок объявления'),
    'description': fields.String(required=True, description='Описание объявления'),
    'price': fields.Float(required=True, description='Цена объявления'),
    'images': fields.List(fields.String, required=True, description='Список ссылок на изображения'),
    'category': fields.String(required=True, description='Категория объявления')
})
user_model = api.model('User', {
    'id': fields.Integer(required=True, description='ID пользователя'),
    'username': fields.String(required=True, description='Имя пользователя'),
    'email': fields.String(required=True, description='Email пользователя'),
})
token_request = api.model('TokenRequest', {
    'user_id': fields.Integer(required=True, description='ID пользователя')
})

token_response = api.model('TokenResponse', {
    'access_token': fields.String(description='Сгенерированный access token')
})

user_full_model = api.model('UserFull', {
    'id': fields.Integer,
    'username': fields.String,
    'is_admin': fields.Boolean,
    'two_factor_secret': fields.String,
    'refresh': fields.String,
    'password_hash': fields.String
})

send_email_model = api.model('SendEmail', {
    'to_email': fields.String(required=True, description='Email получателя'),
    'otp': fields.String(required=True, description='Код подтверждения'),
})

delete_user_model = api.model('DeleteUser', {
    'user_id': fields.Integer(required=True, description='ID пользователя для удаления')
})

update_advertisement_model = api.model('UpdateAdvertisement', {
    'title': fields.String(required=False, description='Новый заголовок объявления'),
    'description': fields.String(required=False, description='Новое описание объявления'),
    'price': fields.Float(required=False, description='Новая цена объявления'),
    'images': fields.List(fields.String, required=False, description='Новый массив ссылок на изображения'),
    'category': fields.String(required=False, description='Новая категория объявления')
})

verify_token_model = api.model('VerifyRefreshToken', {
    'provided_token': fields.String(required=True, description='Предоставленный refresh-токен'),
})

refresh_access_model = api.model('RefreshAccessToken', {
    'provided_refresh_token': fields.String(required=True, description='Refresh токен для обновления access токена'),
})

@api.route('/user/<int:user_id>/refresh-access-token')
class RefreshAccessTokenResource(Resource):
    @api.expect(refresh_access_model)
    def post(self, user_id):
        """
        Обновляет access token с использованием refresh token.
        """
        from app.jwt_utils import refresh_access_token  # если ещё не импортирована

        data = request.json
        provided_refresh_token = data.get('provided_refresh_token')

        if not provided_refresh_token:
            api.abort(400, "Необходим refresh токен")

        new_access_token = refresh_access_token(user_id, provided_refresh_token)
        if not new_access_token:
            api.abort(401, "Refresh токен недействителен")

        return {
            "access_token": new_access_token
        }

@api.route('/user/<int:user_id>/verify-refresh-token')
class VerifyRefreshTokenResource(Resource):
    @api.expect(verify_token_model)
    def post(self, user_id):
        """
        Проверяет, действителен ли предоставленный refresh-токен для пользователя.
        """
        from test_db import verify_refresh_token  # если ещё не импортирована

        data = request.json
        provided_token = data.get('provided_token')

        if not provided_token:
            api.abort(400, "Отсутствует токен для проверки")

        is_valid = verify_refresh_token(user_id, provided_token)
        return {
            "user_id": user_id,
            "is_valid": is_valid
        }, 200 if is_valid else 401
@api.route('/user/<int:user_id>/refresh-token')
class RefreshTokenResource(Resource):
    def post(self, user_id):
        """
        Создать новый refresh-токен для пользователя.
        """
        from test_db import create_refresh_token  # если функция не импортирована

        refresh_token = create_refresh_token(user_id)
        if refresh_token:
            return {
                "message": "Refresh-токен успешно создан.",
                "refresh_token": refresh_token
            }, 200
        else:
            api.abort(404, "Пользователь не найден или произошла ошибка")

@api.route('/user/<int:user_id>/2fa')
class TwoFactorResource(Resource):
    @api.doc(params={'secret': 'Секретный ключ для двухфакторной аутентификации'})
    def post(self, user_id):
        """
        Добавить two-factor secret пользователю.
        """
        secret = request.args.get('secret')
        if not secret:
            api.abort(400, "Секретный ключ обязателен")

        success = add_two_factor_secret(user_id, secret)
        if success:
            return {"message": "Two-factor secret успешно добавлен"}, 200
        else:
            api.abort(404, "Пользователь не найден или произошла ошибка")

    def delete(self, user_id):
        """
        Удалить two-factor secret пользователя.
        """
        success = delete_two_factor_secret(user_id)
        if success:
            return {"message": "Two-factor secret успешно удален"}, 200
        else:
            api.abort(404, "Пользователь не найден или произошла ошибка")

@api.route('/advertisement/<int:advertisement_id>')
class AdvertisementDetailResource(Resource):
    def get(self, advertisement_id):
        """
        Получение данных объявления по ID.
        """
        data = get_advertisement_data(advertisement_id)
        if data:
            return data, 200
        else:
            api.abort(404, "Объявление не найдено")

@api.route('/update-advertisement/<int:advertisement_id>')
class UpdateAdvertisementResource(Resource):
    @api.expect(update_advertisement_model)
    def put(self, advertisement_id):
        """
        Обновляет информацию о существующем объявлении.
        """
        data = request.json
        title = data.get('title')
        description = data.get('description')
        price = data.get('price')
        images = data.get('images')
        category = data.get('category')

        # Обновляем объявление с новым значением
        updated = update_advertisement(advertisement_id, title, description, price, images, category)

        if updated:
            return {'message': 'Объявление успешно обновлено'}, 200
        else:
            api.abort(404, "Объявление не найдено")
@api.route('/user')
class UserResource(Resource):
    @api.doc(params={'field': 'Поле для поиска', 'value': 'Значение для поиска'})
    def get(self):
        """
        Получение пользователя по заданному полю.
        """
        field = request.args.get('field')
        value = request.args.get('value')

        if not field or not value:
            api.abort(400, "Поле и значение должны быть переданы")

        user = get_user_by_field(field, value)
        if user:
            return {
                'id': user.id,
                'username': user.email,
                'email': user.email
            }
        api.abort(404, "Пользователь не найден")


@api.route('/users')
class UsersListResource(Resource):
    @api.doc(params={
        'include_password_hash': 'Включать хэши паролей (true/false)',
        'filter_admins': 'Показать только админов (true/false)'
    })
    def get(self):
        """
        Получение списка всех пользователей с возможностью фильтрации.
        """
        include_hash = request.args.get('include_password_hash', 'false').lower() == 'true'
        filter_admins = request.args.get('filter_admins', 'false').lower() == 'true'

        users = get_all_users(
            include_password_hash=include_hash,
            filter_admins=filter_admins
        )
        return users
@api.route('/generate-token')
class TokenGenerator(Resource):
    @api.expect(token_request)
    @api.marshal_with(token_response)
    def post(self):
        """
        Генерация access token по user_id
        """
        data = request.json
        user_id = data.get('user_id')

        if not user_id:
            api.abort(400, "user_id обязателен")

        token = generate_token(user_id)
        return {'access_token': token}


@api.route('/send-email')
class SendEmailResource(Resource):
    @api.expect(send_email_model)
    def post(self):
        """
        Отправка письма с кодом подтверждения на указанный email.
        """
        data = request.json
        to_email = data.get('to_email')
        otp = data.get('otp')

        if not to_email or not otp:
            api.abort(400, "to_email и otp обязательны")

        try:
            send_email(to_email, otp)
            return {"message": "Письмо успешно отправлено!"}, 200
        except Exception as e:
            return {"error": str(e)}, 500

@api.route('/delete-user')
class DeleteUserResource(Resource):
    @api.expect(delete_user_model)
    def delete(self):
        """
        Удаляет пользователя по указанному ID.
        """
        data = request.json
        user_id = data.get('user_id')

        if not user_id:
            api.abort(400, "user_id обязателен")

        result = delete_user(user_id)  # Важно, что мы используем твою функцию здесь

        if result:
            return {"message": "Пользователь успешно удален"}, 200
        else:
            return {"error": "Пользователь не найден"}, 404

@api.route('/create-advertisement')
class CreateAdvertisementResource(Resource):
    @api.expect(create_advertisement_model)
    def post(self):
        """
        Создает новое объявление.
        """
        data = request.json
        user_id = data.get('user_id')
        title = data.get('title')
        description = data.get('description')
        price = data.get('price')
        images = data.get('images')
        category = data.get('category')

        # Проверяем, что все обязательные параметры переданы
        if not all([user_id, title, description, price, images, category]):
            api.abort(400, "Все поля обязательны для заполнения")

        # Создаем объявление, используя функцию
        new_advertisement = create_advertisement(user_id, title, description, price, images, category)

        # Возвращаем созданное объявление
        return {
            'id': new_advertisement.id,
            'user_id': new_advertisement.user_id,
            'title': new_advertisement.title,
            'description': new_advertisement.description,
            'price': new_advertisement.price,
            'images': new_advertisement.images,
            'category': new_advertisement.category
        }, 201