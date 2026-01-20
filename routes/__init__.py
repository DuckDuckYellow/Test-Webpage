"""
Routes Package - Blueprint Registration

This package organizes Flask routes into modular blueprints for better
code organization and maintainability.
"""

from .main import main_bp
from .blog import blog_bp
from .projects import projects_bp

__all__ = ['main_bp', 'blog_bp', 'projects_bp']
