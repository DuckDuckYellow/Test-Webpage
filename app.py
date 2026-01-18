"""
Newton's Repository - A collection of projects, stories, and experiments
"""
from flask import Flask, render_template, abort, url_for, redirect
from datetime import datetime
import os
import re

app = Flask(__name__)

# ============================================================
# BLOG CATEGORIES
# ============================================================
# Each category represents a different blog series or save.
# Categories contain articles and metadata for display.
# ============================================================

ARTICLES = [
    {
        "id": "part 1",
        "title": "How did we fall so far?",
        "date": "2024-01-15",
        "filename": "article1.txt",
        "part": 1
    },
    {
        "id": "part 2",
        "title": "The struggle is real, or is it?",
        "date": "2024-02-20",
        "filename": "article2.txt",
        "part": 2
    },
    {
        "id": "part 3",
        "title": "Crossing the line",
        "date": "2024-03-10",
        "filename": "article3.txt",
        "part": 3
    },
    {
        "id": "part 4",
        "title": "Out with the old and in with the older",
        "date": "2024-04-05",
        "filename": "article4.txt",
        "part": 4
    },
    {
        "id": "part 5",
        "title": "The Crucible",
        "date": "2024-05-12",
        "filename": "article5.txt",
        "part": 5
    },
    {
        "id": "part 6",
        "title": "Disaster and Triumph",
        "date": "2024-06-01",
        "filename": "article6.txt",
        "part": 6
    },
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_article_content(filename):
    """Read article content from a text file."""
    filepath = os.path.join(app.root_path, "articles", filename)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None


def format_date(date_string):
    """Convert date string to readable format."""
    date_obj = datetime.strptime(date_string, "%Y-%m-%d")
    return date_obj.strftime("%B %d, %Y")


def calculate_reading_time(text):
    """Calculate estimated reading time based on ~200 words per minute."""
    words = len(text.split())
    minutes = max(1, round(words / 200))
    return minutes


def get_excerpt(text, sentence_count=2):
    """Extract first N sentences as a preview excerpt."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    excerpt_sentences = sentences[:sentence_count]
    excerpt = ' '.join(excerpt_sentences)

    if excerpt and excerpt[-1] not in '.!?':
        excerpt += '...'

    if len(excerpt) > 200:
        excerpt = excerpt[:197].rsplit(' ', 1)[0] + '...'

    return excerpt


def parse_content(text):
    """Parse article content into structured blocks (headings and paragraphs)."""
    blocks = []
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    for para in paragraphs:
        is_heading = False

        if re.match(r'^Part\s+\d+', para, re.IGNORECASE):
            is_heading = True
        elif len(para) < 80 and not para.endswith('.') and '\n' not in para:
            if re.match(r'^[A-Z]', para) and not para.endswith(','):
                is_heading = True
        elif para.isupper() and len(para) < 100:
            is_heading = True

        if is_heading:
            blocks.append({"type": "heading", "content": para})
        else:
            blocks.append({"type": "paragraph", "content": para})

    return blocks


def get_category_articles(category_id):
    """Get all articles for a category with metadata."""
    category = BLOG_CATEGORIES.get(category_id)
    if not category:
        return None, []

    articles_with_meta = []
    for article in category["articles"]:
        content = get_article_content(article["filename"])
        if content:
            reading_time = calculate_reading_time(content)
            excerpt = get_excerpt(content)
        else:
            reading_time = 0
            excerpt = ""

        articles_with_meta.append({
            **article,
            "reading_time": reading_time,
            "excerpt": excerpt,
            "category_id": category_id
        })

    sorted_articles = sorted(articles_with_meta, key=lambda x: x["part"])
    return category, sorted_articles


def get_article_by_id(category_id, article_id):
    """Find an article by category and article ID."""
    category = BLOG_CATEGORIES.get(category_id)
    if not category:
        return None, None

    for article in category["articles"]:
        if article["id"] == article_id:
            return category, article

    return category, None


def get_prev_next_articles(category_id, current_part):
    """Get previous and next articles within a category."""
    category = BLOG_CATEGORIES.get(category_id)
    if not category:
        return None, None

    prev_article = None
    next_article = None

    for article in category["articles"]:
        if article["part"] == current_part - 1:
            prev_article = article
        elif article["part"] == current_part + 1:
            next_article = article

    return prev_article, next_article


def get_latest_article():
    """Get the most recent article across all categories."""
    latest = None
    latest_date = None
    latest_category = None

    for cat_id, category in BLOG_CATEGORIES.items():
        for article in category["articles"]:
            article_date = datetime.strptime(article["date"], "%Y-%m-%d")
            if latest_date is None or article_date > latest_date:
                latest = article
                latest_date = article_date
                latest_category = category

    if latest and latest_category:
        content = get_article_content(latest["filename"])
        return {
            **latest,
            "category_id": latest_category["id"],
            "category_name": latest_category["name"],
            "excerpt": get_excerpt(content) if content else "",
            "reading_time": calculate_reading_time(content) if content else 0
        }
    return None


# Make helper functions available in templates
app.jinja_env.globals["format_date"] = format_date


# ============================================================
# ROUTES
# ============================================================

@app.route("/")
def home():
    """Homepage - Newton's Repository landing page."""
    latest_article = get_latest_article()
    return render_template(
        "index.html",
        latest_article=latest_article,
        categories=BLOG_CATEGORIES,
        projects=PROJECTS
    )


@app.route("/blog")
def blog_home():
    """Blog overview - shows all blog categories."""
    categories_with_meta = []
    for cat_id, category in BLOG_CATEGORIES.items():
        article_count = len(category["articles"])
        categories_with_meta.append({
            **category,
            "article_count": article_count
        })

    return render_template(
        "blog_home.html",
        categories=categories_with_meta
    )


@app.route("/blog/<category_id>")
def blog_category(category_id):
    """Blog category page - shows all articles in a category."""
    category, articles = get_category_articles(category_id)

    if category is None:
        abort(404)

    total_parts = len(articles)

    return render_template(
        "blog_category.html",
        category=category,
        articles=articles,
        total_parts=total_parts
    )


@app.route("/blog/<category_id>/<article_id>")
def article(category_id, article_id):
    """Individual article page."""
    category, article_data = get_article_by_id(category_id, article_id)

    if category is None or article_data is None:
        abort(404)

    content = get_article_content(article_data["filename"])
    if content is None:
        abort(404)

    content_blocks = parse_content(content)
    reading_time = calculate_reading_time(content)
    total_parts = len(category["articles"])
    prev_article, next_article = get_prev_next_articles(category_id, article_data["part"])

    return render_template(
        "article.html",
        article=article_data,
        category=category,
        content_blocks=content_blocks,
        reading_time=reading_time,
        prev_article=prev_article,
        next_article=next_article,
        total_parts=total_parts
    )


# Legacy route redirect for old article URLs
@app.route("/article/<article_id>")
def article_legacy(article_id):
    """Redirect old article URLs to new structure."""
    # Find the article in any category
    for cat_id, category in BLOG_CATEGORIES.items():
        for article in category["articles"]:
            if article["id"] == article_id:
                return redirect(url_for('article', category_id=cat_id, article_id=article_id))
    abort(404)


@app.route("/projects")
def projects():
    """Personal projects page."""
    return render_template("projects.html", projects=PROJECTS)


@app.route("/about")
def about():
    """About page."""
    return render_template("about.html")


@app.errorhandler(404)
def page_not_found(e):
    """Custom 404 page."""
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True)
