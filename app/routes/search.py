from flask import Blueprint, request, render_template
from test_db import get_all_advertisements_search

search_bp = Blueprint('search', __name__)

@search_bp.route('/search')
def search():
    category = request.args.get('category', '').strip()
    print(f"Полученная категория: {category}")  # Отладка
    # Очистка и нормализация входных параметров
    query = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    min_price = request.args.get('min_price', '').strip()
    max_price = request.args.get('max_price', '').strip()

    # Преобразуем пустые строки в None
    query = query if query else None
    category = category if category else None
    min_price = min_price if min_price else None
    max_price = max_price if max_price else None

    advertisements = get_all_advertisements_search(
        query=query,
        category=category,
        min_price=min_price,
        max_price=max_price
    )

    all_categories = [
        'Техника',
        'Продукты',
        'Одежда',
        'Книги',
        'Хозтовары'
    ]

    return render_template(
        'search.html',
        advertisements=advertisements,
        query=query or '',
        category=category or '',
        min_price=min_price or '',
        max_price=max_price or '',
        all_categories=all_categories
    )
