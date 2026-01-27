"""
Application configuration with environment-specific settings.

Usage:
    from config import get_config
    app.config.from_object(get_config())
"""
import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory of the application
BASE_DIR = Path(__file__).parent.resolve()


class Config:
    """Base configuration with common settings."""

    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError(
            "SECRET_KEY environment variable is required!\n"
            "Generate one with: python -c 'import secrets; print(secrets.token_hex(32))'"
        )

    # Session configuration
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour

    # File upload settings
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_UPLOAD_SIZE', 10 * 1024 * 1024))  # 10MB default
    UPLOAD_EXTENSIONS = {'.xlsx', '.xls'}

    # Path configuration
    ARTICLES_DIR = BASE_DIR / 'articles'
    STATIC_DIR = BASE_DIR / 'static'
    TEMPLATES_DIR = BASE_DIR / 'templates'

    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f'sqlite:///{BASE_DIR / "newton.db"}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Set to True for SQL query debugging

    # Application settings
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = False


class DevelopmentConfig(Config):
    """Development environment configuration."""

    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False  # Allow HTTP in development

    # Development-specific settings
    EXPLAIN_TEMPLATE_LOADING = False
    SEND_FILE_MAX_AGE_DEFAULT = 0  # Disable caching for development


class ProductionConfig(Config):
    """Production environment configuration."""

    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True  # Require HTTPS

    # Production-specific settings
    PREFERRED_URL_SCHEME = 'https'

    # Additional validation for production
    if not os.environ.get('SECRET_KEY'):
        raise ValueError("SECRET_KEY must be explicitly set in production!")


class TestingConfig(Config):
    """Testing environment configuration."""

    DEBUG = True
    TESTING = True
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = False  # Disable CSRF for testing

    # Testing-specific settings
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # 1MB for tests


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env_name=None):
    """
    Get configuration class for specified environment.

    Args:
        env_name (str): Environment name (development/production/testing)
                       If None, uses FLASK_ENV environment variable

    Returns:
        Config class for the specified environment
    """
    if env_name is None:
        env_name = os.environ.get('FLASK_ENV', 'development')

    return config.get(env_name, config['default'])
