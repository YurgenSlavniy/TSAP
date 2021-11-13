from flask import Flask
from dotenv import load_dotenv

# Controllers.
from app.controller.home import bp as home

#
import os

# Aвтоматичкская установка переменных окружения
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

controllers = [
    home,
]


def create_app()-> "flask":
    app = Flask(__name__, static_folder="web", template_folder="view")

    for c in controllers:
        app.register_blueprint(c)

    return app
