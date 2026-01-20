"""
Main Routes Blueprint

Handles homepage, about, and other static pages.
"""

from flask import Blueprint, render_template, current_app

main_bp = Blueprint('main', __name__)


@main_bp.route("/")
def home():
    """Homepage with latest blog article and project overview."""
    from app import BLOG_CATEGORIES, PROJECTS, blog_service

    latest_article = blog_service.get_latest_article(BLOG_CATEGORIES)
    return render_template(
        "index.html",
        latest_article=latest_article,
        categories=BLOG_CATEGORIES,
        projects=PROJECTS
    )


@main_bp.route("/about")
def about():
    """About page."""
    return render_template("about.html")


@main_bp.errorhandler(404)
def page_not_found(e):
    """Custom 404 error page."""
    return render_template("404.html"), 404
