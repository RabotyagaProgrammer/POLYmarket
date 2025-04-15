from flask import Flask
from database import db  # Импортируем объект db из файла database
from test_db import *

# Инициализация приложения Flask
app = Flask(__name__)

# Настройка подключения к базе данных (SQLite для примера)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация базы данных с приложением
db.init_app(app)

# Создание всех таблиц в базе данных
with app.app_context():
    db.create_all()
    delete_all_users()
    create_user('test1', '228')
    #print(get_all_users())
    #print(get_user_data('test2'))
    #print(verify_password('test1', '228'))
    change_password('test1', '228', '337')
    #print(verify_password('test1', '228'))
    #print(verify_password('test1', '337'))
    # print(get_all_users())

if __name__ == '__main__':
    app.run(debug=False)
