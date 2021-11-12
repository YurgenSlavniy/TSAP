from flask import Blueprint

bp = Blueprint("home", __name__)


@bp.route("/")
def index()-> str:
    return "start page"