"""
Newton's Repository - A collection of projects, stories, and experiments
"""
from flask import Flask, render_template, abort, url_for, redirect, request
from datetime import datetime
import os
import re

app = Flask(__name__)

BLOG_CATEGORIES = {
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

PROJECTS = [
    {"id": "capacity-tracker", "name": "Recruitment Capacity Tracker", "description": "Calculate team capacity for recruitment workloads.", "status": "active", "url": "/projects/capacity-tracker"},
    {"id": "meal-generator", "name": "Meal Generator", "description": "A tool to help plan weekly meals.", "status": "planned"},
    {"id": "fm-tools", "name": "FM Analytics Tools", "description": "Utilities for analyzing FM save data.", "status": "planned"},
]

def get_article_content(filename):
    filepath = os.path.join(app.root_path, "articles", filename)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None

def format_date(date_string):
    date_obj = datetime.strptime(date_string, "%Y-%m-%d")
    return date_obj.strftime("%B %d, %Y")

def calculate_reading_time(text):
    words = len(text.split())
    return max(1, round(words / 200))

def get_excerpt(text, sentence_count=2):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    excerpt = ' '.join(sentences[:sentence_count])
    if len(excerpt) > 200:
        excerpt = excerpt[:197] + '...'
    return excerpt

def parse_content(text):
    blocks = []
    for para in [p.strip() for p in text.split("\n\n") if p.strip()]:
        is_heading = re.match(r'^Part\s+\d+', para, re.IGNORECASE) or (len(para) < 80 and not para.endswith('.'))
        blocks.append({"type": "heading" if is_heading else "paragraph", "content": para})
    return blocks

def get_category_articles(category_id):
    category = BLOG_CATEGORIES.get(category_id)
    if not category:
        return None, []
    articles = []
    for article in category["articles"]:
        content = get_article_content(article["filename"])
        articles.append({**article, "reading_time": calculate_reading_time(content) if content else 0, "excerpt": get_excerpt(content) if content else "", "category_id": category_id})
    return category, sorted(articles, key=lambda x: x["part"])

def get_article_by_id(category_id, article_id):
    category = BLOG_CATEGORIES.get(category_id)
    if not category:
        return None, None
    for article in category["articles"]:
        if article["id"] == article_id:
            return category, article
    return category, None

def get_prev_next_articles(category_id, current_part):
    category = BLOG_CATEGORIES.get(category_id)
    if not category:
        return None, None
    prev_article, next_article = None, None
    for article in category["articles"]:
        if article["part"] == current_part - 1:
            prev_article = article
        elif article["part"] == current_part + 1:
            next_article = article
    return prev_article, next_article

def get_latest_article():
    latest, latest_date, latest_category = None, None, None
    for cat_id, category in BLOG_CATEGORIES.items():
        for article in category["articles"]:
            article_date = datetime.strptime(article["date"], "%Y-%m-%d")
            if latest_date is None or article_date > latest_date:
                latest, latest_date, latest_category = article, article_date, category
    if latest and latest_category:
        content = get_article_content(latest["filename"])
        return {**latest, "category_id": latest_category["id"], "category_name": latest_category["name"], "excerpt": get_excerpt(content) if content else "", "reading_time": calculate_reading_time(content) if content else 0}
    return None

# ========== RECRUITMENT CAPACITY TRACKER FUNCTIONS ==========

def calculate_recruiter_capacity(easy_vacancies, medium_vacancies, hard_vacancies):
    """
    Calculate capacity usage for a recruiter based on vacancy counts.

    Business rules:
    - Easy vacancies: Max 30 at full capacity
    - Medium vacancies: Max 20 at full capacity
    - Hard vacancies: Max 12 at full capacity

    Args:
        easy_vacancies (int): Number of easy vacancies
        medium_vacancies (int): Number of medium vacancies
        hard_vacancies (int): Number of hard vacancies

    Returns:
        dict: Contains capacity_used (0-1+), capacity_percentage, status, remaining capacities
    """
    # Calculate capacity used (can exceed 1.0 if overloaded)
    capacity_used = (easy_vacancies / 30) + (medium_vacancies / 20) + (hard_vacancies / 12)
    capacity_percentage = round(capacity_used * 100, 1)

    # Determine status based on capacity
    if capacity_used > 1.0:
        status = 'overloaded'
        status_text = 'Overloaded'
    elif capacity_used >= 0.9:
        status = 'at-capacity'
        status_text = 'At Capacity'
    elif capacity_used >= 0.7:
        status = 'near-capacity'
        status_text = 'Near Capacity'
    else:
        status = 'available'
        status_text = 'Available'

    # Calculate remaining capacity for additional work
    remaining_capacity = 1.0 - capacity_used

    if remaining_capacity >= 0:
        additional_easy = max(0, int(remaining_capacity * 30))
        additional_medium = max(0, int(remaining_capacity * 20))
        additional_hard = max(0, int(remaining_capacity * 12))
        remaining_message = f"Can take {additional_easy} more easy OR {additional_medium} more medium OR {additional_hard} more hard vacancies"
    else:
        # Overloaded - calculate how much over
        overload = abs(remaining_capacity)
        overload_easy = int(overload * 30)
        overload_medium = int(overload * 20)
        overload_hard = int(overload * 12)
        remaining_message = f"Overloaded by {overload_easy} easy OR {overload_medium} medium OR {overload_hard} hard vacancies"

    return {
        'capacity_used': capacity_used,
        'capacity_percentage': capacity_percentage,
        'status': status,
        'status_text': status_text,
        'remaining_message': remaining_message,
        'remaining_capacity': remaining_capacity
    }

def calculate_team_summary(recruiters_data):
    """
    Calculate team-wide summary statistics.

    Args:
        recruiters_data (list): List of recruiter dictionaries with capacity info

    Returns:
        dict: Team summary with counts and averages
    """
    if not recruiters_data:
        return None

    total_recruiters = len(recruiters_data)
    total_capacity = sum(r['capacity_percentage'] for r in recruiters_data)
    average_capacity = round(total_capacity / total_recruiters, 1)

    # Count by status
    status_counts = {
        'available': sum(1 for r in recruiters_data if r['status'] == 'available'),
        'near-capacity': sum(1 for r in recruiters_data if r['status'] == 'near-capacity'),
        'at-capacity': sum(1 for r in recruiters_data if r['status'] == 'at-capacity'),
        'overloaded': sum(1 for r in recruiters_data if r['status'] == 'overloaded')
    }

    # Determine overall team health
    if status_counts['overloaded'] > total_recruiters * 0.3:
        team_health = 'critical'
        team_health_text = 'Critical - Team Overloaded'
    elif status_counts['at-capacity'] + status_counts['overloaded'] > total_recruiters * 0.5:
        team_health = 'warning'
        team_health_text = 'Warning - High Utilization'
    elif average_capacity < 50:
        team_health = 'underutilized'
        team_health_text = 'Good - Capacity Available'
    else:
        team_health = 'healthy'
        team_health_text = 'Healthy - Balanced Load'

    return {
        'total_recruiters': total_recruiters,
        'average_capacity': average_capacity,
        'status_counts': status_counts,
        'team_health': team_health,
        'team_health_text': team_health_text
    }

app.jinja_env.globals["format_date"] = format_date

@app.route("/")
def home():
    return render_template("index.html", latest_article=get_latest_article(), categories=BLOG_CATEGORIES, projects=PROJECTS)

@app.route("/blog")
def blog_home():
    categories = [{**cat, "article_count": len(cat["articles"])} for cat_id, cat in BLOG_CATEGORIES.items()]
    return render_template("blog_home.html", categories=categories)

@app.route("/blog/<category_id>")
def blog_category(category_id):
    category, articles = get_category_articles(category_id)
    if not category:
        abort(404)
    return render_template("blog_category.html", category=category, articles=articles, total_parts=len(articles))

@app.route("/blog/<category_id>/<article_id>")
def article(category_id, article_id):
    category, article_data = get_article_by_id(category_id, article_id)
    if not category or not article_data:
        abort(404)
    content = get_article_content(article_data["filename"])
    if not content:
        abort(404)
    prev_article, next_article = get_prev_next_articles(category_id, article_data["part"])
    return render_template("article.html", article=article_data, category=category, content_blocks=parse_content(content), reading_time=calculate_reading_time(content), prev_article=prev_article, next_article=next_article, total_parts=len(category["articles"]))

@app.route("/article/<article_id>")
def article_legacy(article_id):
    for cat_id, category in BLOG_CATEGORIES.items():
        for article in category["articles"]:
            if article["id"] == article_id:
                return redirect(url_for('article', category_id=cat_id, article_id=article_id))
    abort(404)

@app.route("/projects")
def projects():
    return render_template("projects.html", projects=PROJECTS)

@app.route("/projects/capacity-tracker", methods=["GET", "POST"])
def capacity_tracker():
    """
    Recruitment Capacity Tracker tool.

    GET: Display the input form
    POST: Process form data and display results
    """
    recruiters_data = []
    team_summary = None
    errors = []

    if request.method == "POST":
        # Get the number of recruiters from form
        num_recruiters = 0

        # Collect all recruiter data from form
        # Form fields are named: name_0, easy_0, medium_0, hard_0, name_1, easy_1, etc.
        index = 0
        while f'name_{index}' in request.form:
            name = request.form.get(f'name_{index}', '').strip()

            # Skip if name is empty
            if not name:
                index += 1
                continue

            try:
                easy = int(request.form.get(f'easy_{index}', 0))
                medium = int(request.form.get(f'medium_{index}', 0))
                hard = int(request.form.get(f'hard_{index}', 0))

                # Validate non-negative
                if easy < 0 or medium < 0 or hard < 0:
                    errors.append(f"Error for {name}: Vacancy counts cannot be negative")
                    index += 1
                    continue

                # Calculate capacity for this recruiter
                capacity_info = calculate_recruiter_capacity(easy, medium, hard)

                recruiter = {
                    'name': name,
                    'easy_vacancies': easy,
                    'medium_vacancies': medium,
                    'hard_vacancies': hard,
                    **capacity_info
                }

                recruiters_data.append(recruiter)

            except ValueError:
                errors.append(f"Error for {name}: Please enter valid numbers")

            index += 1

        # Calculate team summary if we have data
        if recruiters_data:
            team_summary = calculate_team_summary(recruiters_data)

    return render_template(
        "projects/capacity_tracker.html",
        recruiters=recruiters_data,
        team_summary=team_summary,
        errors=errors
    )

@app.route("/about")
def about():
    return render_template("about.html")

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

if __name__ == "__main__":
    app.run(debug=True)
