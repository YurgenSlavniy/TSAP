from flask import Flask, json, render_template
from dotenv import load_dotenv

# Controllers.
from app.controllers.home import bp as home
from app.controllers.csv_handler import bp as csv_handler

#
import os

# Aвтоматичкская установка переменных окружения
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# Обработчики приложения
controllers = [
    home,
    csv_handler,
]

# Если нет папки uploads
if not os.path.isdir("uploads"):
    os.mkdir("uploads")

def page_not_found(e):
    '''Если набран не существующий адрес'''
    return render_template('404.html'), 404


def create_app()-> "flask":
    '''Создает объект проложения'''
    app = Flask(__name__, static_folder="web", template_folder="views")

    # Конфигурация приложения 
    app.config.update(
        SECRET_KEY="...",
        UPLOAD_FOLDER="uploads",
        MAX_CONTENT_LENGTH=10000000,
    )

    # Регистрация обработчика не существующей страницы
    app.register_error_handler(404, page_not_found)

    # Регистрация контроллеров
    for c in controllers:
        app.register_blueprint(c)
    
    return app
