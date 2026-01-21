from flask import Blueprint, render_template

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    # `profile` is injected via the app context processor
    return render_template("index.html")
