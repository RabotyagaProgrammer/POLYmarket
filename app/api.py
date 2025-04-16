from flask_restx import Api, Resource, fields
from flask import Blueprint, request
from test_db import get_user_by_field

api_bp = Blueprint('api', __name__)
api = Api(api_bp, version='1.0', title='User API',
          description='API для работы с пользователями')

user_model = api.model('User', {
    'id': fields.Integer(required=True, description='ID пользователя'),
    'username': fields.String(required=True, description='Имя пользователя'),
    'email': fields.String(required=True, description='Email пользователя'),
})

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
                'username': user.username,
                'email': user.username
            }
        api.abort(404, "Пользователь не найден")