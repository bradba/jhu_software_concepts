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
    "bio": """Brad Ballinger is a senior engineering professional known for owning and delivering critical, high-impact technical initiatives. He approaches engineering with a strong product-aware mindset, recognizing how deeply technology decisions influence the business, and ensures that both company and team priorities stay aligned throughout execution.

His expertise spans distributed systems, backend system design, open-source design practices, and the documentation standards needed to support long-lived platforms. Brad is frequently the go-to engineer for architecting and executing seamless live migrations and production rollouts, especially when system continuity is non-negotiable.

With a deep interest in mathematics and data, Brad works effectively across engineering and data science organizations, particularly on projects involving large and complex datasets. This cross-domain fluency enables him to bridge gaps, accelerate delivery, and contribute meaningfully to analytical and ML-adjacent efforts.
""",
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
