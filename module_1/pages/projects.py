from flask import Blueprint, render_template

projects_bp = Blueprint("projects", __name__, url_prefix="/projects")


@projects_bp.route("/")
def projects():
    # Renders overview of projects
    return render_template("projects.html")


@projects_bp.route("/module1")
def module1_detail():
    # Sub-page for Module 1 detailed view
    return render_template("module1.html")
