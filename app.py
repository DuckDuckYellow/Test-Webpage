"""
Newton's Repository - A collection of projects, stories, and experiments

Application factory pattern with blueprints for modular architecture.
"""

from flask import Flask
from datetime import datetime
from pathlib import Path
import os
from config import get_config
from models import Article, BlogCategory
from services import BlogService, CapacityService, FileService
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from extensions import csrf, limiter

# Initialize extensions (will be attached to app in create_app)
# csrf and limiter are now imported from extensions.py

# Global data structures (accessible to blueprints via app context)
BLOG_CATEGORIES = {}
PROJECTS = []

# Global services (initialized in create_app, accessible to blueprints)
blog_service = None
capacity_service = None
file_service = None
league_baselines = None


def format_date(date_string):
    """Format date string for Jinja templates."""
    date_obj = datetime.strptime(date_string, "%Y-%m-%d")
    return date_obj.strftime("%B %d, %Y")


def initialize_league_baselines(app):
    """
    Load league wage baselines from JSON file on startup.

    If the baseline file exists, loads it into the global league_baselines variable.
    If missing, logs a warning but continues (feature will be disabled).
    """
    global league_baselines
    baseline_path = os.path.join(os.path.dirname(__file__), 'data', 'league_baselines.json')

    if os.path.exists(baseline_path):
        try:
            from services.league_baseline_generator import LeagueBaselineGenerator
            generator = LeagueBaselineGenerator()
            league_baselines = generator.load_from_json(baseline_path)
            app.logger.info(
                f"Loaded {len(league_baselines.baselines)} league baselines from "
                f"{len(league_baselines.get_available_divisions())} divisions "
                f"(GK multiplier: {league_baselines.gk_wage_multiplier:.3f})"
            )
        except Exception as e:
            app.logger.error(f"Failed to load league baselines: {e}")
            league_baselines = None
    else:
        app.logger.warning(
            f"League baseline data not found at {baseline_path} - "
            "league value comparisons will not be available"
        )


def create_app(config_class=None):
    """
    Application Factory Pattern.

    Creates and configures the Flask application with all extensions,
    blueprints, and services.

    Args:
        config_class: Configuration class to use (defaults to environment-based)

    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)

    # Load configuration
    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)

    # Initialize extensions
    csrf.init_app(app)
    limiter.init_app(app)

    # Setup professional logging
    from utils.logger import setup_logger
    setup_logger(app)

    # Initialize global services
    global blog_service, capacity_service, file_service, league_baselines
    blog_service = BlogService(app.config['ARTICLES_DIR'])
    capacity_service = CapacityService()
    file_service = FileService(
        upload_extensions=app.config['UPLOAD_EXTENSIONS'],
        max_content_length=app.config['MAX_CONTENT_LENGTH']
    )

    app.logger.info("Services initialized successfully")

    # Initialize league baselines
    initialize_league_baselines(app)

    # Initialize global data structures
    initialize_blog_categories()
    initialize_projects()

    # Register security headers
    register_security_headers(app)

    # Register blueprints
    register_blueprints(app)

    # Register Jinja globals
    app.jinja_env.globals["format_date"] = format_date

    app.logger.info("Application factory completed - app ready")

    return app


def initialize_blog_categories():
    """Initialize blog categories and articles."""
    global BLOG_CATEGORIES

    # Raw category data for initialization
    _RAW_CATEGORIES = {
        "morecambe-fm26": {
            "id": "morecambe-fm26",
            "name": "Morecambe FC",
            "subtitle": "FM26 Save",
            "description": "Following Morecambe FC from administration to glory.",
            "image": "morecambe-logo.png",
            "articles": [
                {"id": "the-journey-begins", "title": "How did we fall so far?", "date": "2024-01-15", "filename": "article1.txt", "part": 1},
                {"id": "first-season-struggles", "title": "The struggle is real, or is it?", "date": "2024-02-20", "filename": "article2.txt", "part": 2},
                {"id": "transfer-window-rebuild", "title": "Crossing the line", "date": "2024-03-10", "filename": "article3.txt", "part": 3},
                {"id": "turning-point", "title": "Out with the old and in with the older", "date": "2024-04-05", "filename": "article4.txt", "part": 4},
                {"id": "promotion-push", "title": "The Crucible", "date": "2024-05-12", "filename": "article5.txt", "part": 5},
                {"id": "glory-day", "title": "Disaster and Triumph", "date": "2024-06-01", "filename": "article6.txt", "part": 6},
            ]
        }
    }

    # Convert raw data to typed BlogCategory objects
    for cat_id, data in _RAW_CATEGORIES.items():
        articles = [Article(**article, category_id=cat_id) for article in data['articles']]
        BLOG_CATEGORIES[cat_id] = BlogCategory(
            id=data['id'],
            name=data['name'],
            subtitle=data['subtitle'],
            description=data['description'],
            image=data['image'],
            articles=articles
        )


def initialize_projects():
    """Initialize projects list."""
    global PROJECTS

    PROJECTS.extend([
        {
            "id": "capacity-tracker",
            "name": "Recruitment Capacity Tracker",
            "description": "Calculate team capacity for recruitment workloads.",
            "status": "active",
            "url": "/projects/capacity-tracker"
        },
        {
            "id": "squad-audit-tracker",
            "name": "Squad Audit Tracker",
            "description": "Analyze FM squads with per-90 metrics and value scoring.",
            "status": "active",
            "url": "/projects/squad-audit-tracker"
        },
        {
            "id": "meal-generator",
            "name": "Meal Generator",
            "description": "A tool to help plan weekly meals.",
            "status": "planned"
        },
        {
            "id": "fm-tools",
            "name": "FM Analytics Tools",
            "description": "Utilities for analyzing FM save data.",
            "status": "planned"
        },
    ])


def register_security_headers(app):
    """Register security headers for all responses."""

    @app.after_request
    def set_security_headers(response):
        """Apply security headers to all responses."""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'

        if app.config.get('PREFERRED_URL_SCHEME') == 'https':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "connect-src 'self'; "
            "frame-ancestors 'self'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'

        return response


def register_blueprints(app):
    """Register all application blueprints."""
    from routes import main_bp, blog_bp, projects_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(blog_bp)
    app.register_blueprint(projects_bp)

    # Apply rate limiting to sensitive routes
    limiter.limit("10 per minute")(projects_bp)

    app.logger.info("Blueprints registered successfully")


# Application instance for production deployment
app = create_app()


if __name__ == "__main__":
    # Development server
    env_name = os.environ.get('FLASK_ENV', 'development')

    # Display startup information
    print("=" * 60)
    print(f"Flask Application Starting")
    print(f"Environment: {env_name}")
    print(f"Debug Mode: {app.debug}")
    print(f"Config: {app.config.__class__.__name__}")
    print("=" * 60)

    if app.debug and env_name == 'production':
        print("\n⚠️  WARNING: Debug mode enabled in production!")
        print("This is a security risk. Set FLASK_DEBUG=false\n")

    # Get host and port from environment or use defaults
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', 5000))

    app.run(host=host, port=port, debug=app.debug)
