# Базовый образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем всё содержимое проекта в контейнер
COPY . .

# Открываем порт (например, если это веб-приложение)
EXPOSE 8000

# Устанавливаем переменные окружения (если нужно)
ENV FLASK_APP=run.py

# Команда запуска приложения
CMD ["python", "run.py"]
