from flask import Blueprint, render_template

bp = Blueprint("home", __name__)


@bp.route("/")
def index()-> str:
    return render_template("home.html")

@bp.route("/statistic")
def stat_page():
    return render_template("statistic.html")
