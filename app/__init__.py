from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from app.database import db

# Инициализация расширений без привязки к app (application factory)




def create_app():
    """
    Фабричная функция для создания Flask приложения.
    """
    app = Flask(__name__)

    # Конфигурация приложения
    app.config['SECRET_KEY'] = 'supersecretkey'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Инициализация расширений
    db.init_app(app)


    # Регистрация блюпринтов
    from .routes.auth import auth_bp
    from .routes.main import main_bp
    from .api import api_bp
    from .routes.admin_routes import  admin_bp
    from .routes.search import search_bp
    from .routes.profile_routes import profile_bp
    from .routes.advertisment import advertisement_bp


    app.register_blueprint(profile_bp)
    app.register_blueprint(advertisement_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    return app