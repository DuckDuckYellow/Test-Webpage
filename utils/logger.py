"""
Professional Logging Setup

Provides centralized logging configuration for the Flask application
with structured output and request tracking.
"""

import logging
import sys
from flask import request, has_request_context


def setup_logger(app):
    """
    Configure professional logging for the Flask application.

    Sets up:
    - Structured log format with timestamps
    - Console output to stdout
    - Request logging for all incoming HTTP requests
    - Appropriate log level based on environment

    Args:
        app: Flask application instance
    """
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)

    # Create formatter with detailed structure
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)

    # Configure app logger
    app.logger.addHandler(handler)

    # Set log level based on debug mode
    if app.debug:
        app.logger.setLevel(logging.DEBUG)
    else:
        app.logger.setLevel(logging.INFO)

    # Prevent duplicate logs from propagating
    app.logger.propagate = False

    @app.before_request
    def log_request_info():
        """Log incoming request details."""
        if has_request_context():
            app.logger.info(
                f"Request: {request.method} {request.path} "
                f"from {request.remote_addr} "
                f"[User-Agent: {request.user_agent.string[:50]}...]"
            )

    @app.after_request
    def log_response_info(response):
        """Log response status."""
        if has_request_context():
            app.logger.info(
                f"Response: {response.status_code} for "
                f"{request.method} {request.path}"
            )
        return response

    # Log startup
    app.logger.info(f"Logging configured - Level: {logging.getLevelName(app.logger.level)}")

    return app
