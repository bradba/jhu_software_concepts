import os
from flask import Flask
from module_1.pages import main_bp, projects_bp

# Set template and static folders to point to the repository-level folders
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)

# Application data shared to templates via context processor
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


@app.context_processor
def inject_globals():
    return {"profile": profile, "module1": module1}


# Register blueprints
app.register_blueprint(main_bp)
app.register_blueprint(projects_bp)


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8080"))
    app.run(debug=True, host=host, port=port)
