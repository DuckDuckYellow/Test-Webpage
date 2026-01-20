"""
Blog Routes Blueprint

Handles all blog-related routes including categories, articles, and navigation.
"""

from flask import Blueprint, render_template, abort, redirect, url_for, current_app

blog_bp = Blueprint('blog', __name__, url_prefix='/blog')


@blog_bp.route("/")
def blog_home():
    """Blog home page showing all categories."""
    from app import BLOG_CATEGORIES

    categories = list(BLOG_CATEGORIES.values())
    current_app.logger.info(f"Blog home accessed - {len(categories)} categories")
    return render_template("blog_home.html", categories=categories)


@blog_bp.route("/<category_id>")
def blog_category(category_id):
    """Display all articles in a specific category."""
    from app import BLOG_CATEGORIES, blog_service

    category = BLOG_CATEGORIES.get(category_id)
    if not category:
        current_app.logger.warning(f"Category not found: {category_id}")
        abort(404)

    articles = blog_service.get_category_articles(category)
    current_app.logger.info(f"Category '{category.name}' accessed - {len(articles)} articles")

    return render_template(
        "blog_category.html",
        category=category,
        articles=articles,
        total_parts=len(articles)
    )


@blog_bp.route("/<category_id>/<article_id>")
def article(category_id, article_id):
    """Display a specific article with navigation."""
    from app import BLOG_CATEGORIES, blog_service

    category = BLOG_CATEGORIES.get(category_id)
    if not category:
        current_app.logger.warning(f"Category not found: {category_id}")
        abort(404)

    article_data = category.get_article_by_id(article_id)
    if not article_data:
        current_app.logger.warning(f"Article not found: {article_id} in {category_id}")
        abort(404)

    content = blog_service.get_article_content(article_data.filename)
    if not content:
        current_app.logger.error(f"Content file not found: {article_data.filename}")
        abort(404)

    prev_article, next_article = blog_service.get_prev_next_articles(category, article_data.part)
    content_blocks = blog_service.parse_content(content)
    reading_time = blog_service.calculate_reading_time(content)

    current_app.logger.info(f"Article accessed: {article_id} in {category_id}")

    return render_template(
        "article.html",
        article=article_data,
        category=category,
        content_blocks=content_blocks,
        reading_time=reading_time,
        prev_article=prev_article,
        next_article=next_article,
        total_parts=len(category.articles)
    )


@blog_bp.route("/article/<article_id>")
def article_legacy(article_id):
    """Legacy route redirect for old article URLs."""
    from app import BLOG_CATEGORIES

    for cat_id, category in BLOG_CATEGORIES.items():
        for article in category.articles:
            if article.id == article_id:
                current_app.logger.info(f"Legacy redirect: {article_id} -> {cat_id}")
                return redirect(url_for('blog.article', category_id=cat_id, article_id=article_id))

    current_app.logger.warning(f"Legacy article not found: {article_id}")
    abort(404)
