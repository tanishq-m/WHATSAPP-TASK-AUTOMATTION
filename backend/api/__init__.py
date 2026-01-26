"""
API package for WhatsApp Task Manager.
Contains all route blueprints for the application.
"""

from flask import Blueprint

# Import blueprints
from api.employees import employees_bp
from api.projects import projects_bp
from api.tasks import tasks_bp
from api.whatsapp import whatsapp_bp
from api.webhooks import webhooks_bp

# List of all blueprints to register
all_blueprints = [
    (employees_bp, '/api'),
    (projects_bp, '/api'),
    (tasks_bp, '/api'),
    (whatsapp_bp, '/api'),
    (webhooks_bp, '/api'),
]


def register_blueprints(app):
    """
    Register all API blueprints with the Flask app.
    
    Args:
        app: Flask application instance
    """
    for blueprint, url_prefix in all_blueprints:
        app.register_blueprint(blueprint, url_prefix=url_prefix)
        print(f"✅ Registered blueprint: {blueprint.name} at {url_prefix}")
