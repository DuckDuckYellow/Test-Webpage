"""
Flask Blog - A simple blog for Football Manager stories
"""
from flask import Flask, render_template, abort
from datetime import datetime
import os
import re

app = Flask(__name__)

# ============================================================
# ARTICLES DATA
# ============================================================
# Articles are ordered by part number (1-6).
# The 'part' field is used for navigation and display.
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

# Total number of parts in the series
TOTAL_PARTS = len(ARTICLES)


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
    # Split by sentence-ending punctuation followed by space
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    excerpt_sentences = sentences[:sentence_count]
    excerpt = ' '.join(excerpt_sentences)

    # Ensure it ends with proper punctuation
    if excerpt and not excerpt[-1] in '.!?':
        excerpt += '...'

    # Limit length to ~200 characters for card display
    if len(excerpt) > 200:
        excerpt = excerpt[:197].rsplit(' ', 1)[0] + '...'

    return excerpt


def parse_content(text):
    """
    Parse article content, converting to structured blocks.

    Detects:
    - Section headings (lines that look like headers)
    - Regular paragraphs

    Heading patterns detected:
    - Lines starting with "Part X"
    - Lines that are short (<80 chars), end without period, and are standalone
    - Lines in ALL CAPS
    """
    blocks = []
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    for para in paragraphs:
        # Check if this paragraph looks like a heading
        is_heading = False

        # Pattern 1: Starts with "Part" followed by number
        if re.match(r'^Part\s+\d+', para, re.IGNORECASE):
            is_heading = True

        # Pattern 2: Short line, no ending period, likely a section title
        elif len(para) < 80 and not para.endswith('.') and '\n' not in para:
            # Additional check: contains typical heading words or is title-like
            if re.match(r'^[A-Z]', para) and not para.endswith(','):
                is_heading = True

        # Pattern 3: ALL CAPS line
        elif para.isupper() and len(para) < 100:
            is_heading = True

        if is_heading:
            blocks.append({"type": "heading", "content": para})
        else:
            blocks.append({"type": "paragraph", "content": para})

    return blocks


def get_article_by_part(part_number):
    """Get article data by part number."""
    for article in ARTICLES:
        if article["part"] == part_number:
            return article
    return None


def get_prev_next_articles(current_part):
    """Get previous and next articles for navigation."""
    prev_article = get_article_by_part(current_part - 1)
    next_article = get_article_by_part(current_part + 1)
    return prev_article, next_article


# Make helper functions available in templates
app.jinja_env.globals["format_date"] = format_date


@app.route("/")
def home():
    """Homepage - list all articles with metadata."""
    articles_with_meta = []

    for article in ARTICLES:
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
            "excerpt": excerpt
        })

    # Sort by part number (chronological order for a series)
    sorted_articles = sorted(articles_with_meta, key=lambda x: x["part"])

    return render_template(
        "index.html",
        articles=sorted_articles,
        total_parts=TOTAL_PARTS
    )


@app.route("/article/<article_id>")
def article(article_id):
    """Individual article page with navigation."""
    # Find the article
    article_data = None
    for a in ARTICLES:
        if a["id"] == article_id:
            article_data = a.copy()
            break

    if article_data is None:
        abort(404)

    # Get the article content
    content = get_article_content(article_data["filename"])
    if content is None:
        abort(404)

    # Parse content into blocks (paragraphs and headings)
    content_blocks = parse_content(content)

    # Calculate reading time
    reading_time = calculate_reading_time(content)

    # Get previous/next articles for navigation
    prev_article, next_article = get_prev_next_articles(article_data["part"])

    return render_template(
        "article.html",
        article=article_data,
        content_blocks=content_blocks,
        reading_time=reading_time,
        prev_article=prev_article,
        next_article=next_article,
        total_parts=TOTAL_PARTS
    )


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
