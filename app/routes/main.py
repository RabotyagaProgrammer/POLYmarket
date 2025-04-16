from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/profile')
def profile():
    return "<h2>Страница профиля (заглушка)</h2>"

@main_bp.route('/category/<category_name>')
def category(category_name):
    return f"<h2>Категория: {category_name.capitalize()} (заглушка)</h2>"
