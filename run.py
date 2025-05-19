from app import create_app
from app.database import db
from test_db import *

app = create_app()

with app.app_context():
    db.create_all()  # создаст таблицы, если их нет
    # delete_all_users()
    # ads_data = [
    #     {
    #         "title": "Продаю велосипед",
    #         "description": "Отличный горный велосипед, почти не использовался.",
    #         "price": 15000.0,
    #         "images": ["https://example.com/bike1.jpg"],
    #         "category": "Транспорт"
    #     },
    #     {
    #         "title": "Учебники по математике",
    #         "description": "Комплект учебников 10–11 класс, в хорошем состоянии.",
    #         "price": 1200.0,
    #         "images": ["https://example.com/books.jpg"],
    #         "category": "Книги"
    #     }
    # ]
    #
    # # Добавим объявления
    # for ad in ads_data:
    #     create_advertisement(
    #         user_id=1,
    #         title=ad["title"],
    #         description=ad["description"],
    #         price=ad["price"],
    #         images=ad["images"],
    #         category=ad["category"]
    #     )

    #create_user('admin@gmail.com', 'admin', 'admin',True)
if __name__ == '__main__':
    app.run(debug=True)

