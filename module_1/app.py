import os
from flask import Flask, render_template, url_for

# Set template and static folders to point to the repository-level folders
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)

profile = {
    "name": "Brad Ballinger",
    "position": "Software Developer",
    "bio": "I build reliable, testable Python software and enjoy clean design. This portfolio highlights projects from my coursework and personal work. Replace this text with your own bio.",
    "email": "brad.ballinger@gmail.com",
    "linkedin": "https://www.linkedin.com/in/bradballinger/",
    "image": "images/profile.jpg",
}

module1 = {
    "title": "Module 1: Data Processing Pipeline",
    "details": "This project demonstrates reading, cleaning, and summarizing datasets with a small pipeline. It includes parsing inputs, validation, and unit tests.",
    "github": "https://github.com/bradba/jhu_software_concepts",
}


@app.route("/")
def index():
    return render_template("index.html", profile=profile)


@app.route("/projects")
def projects():
    return render_template("projects.html", profile=profile, module1=module1)


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8080"))
    app.run(debug=True, host=host, port=port)
