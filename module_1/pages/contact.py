from flask import Blueprint, render_template

contact_bp = Blueprint("contact", __name__, url_prefix="/contact")


@contact_bp.route("/")
def contact():
    # Simple contact page; contact details injected via context processor
    return render_template("contact.html")
