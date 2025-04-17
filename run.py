from app import create_app
from app.database import db
from test_db import *

app = create_app()

with app.app_context():
    db.create_all()  # создаст таблицы, если их нет
    delete_all_users()
  
    create_user('lobastiyartem@gmail.com', 'maria123', False)
if __name__ == '__main__':
    app.run(debug=True)
