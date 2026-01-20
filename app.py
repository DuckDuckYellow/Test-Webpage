"""
Newton's Repository - A collection of projects, stories, and experiments
"""
from flask import Flask, render_template, abort, url_for, redirect, request, send_file
from datetime import datetime
from pathlib import Path
from io import BytesIO
import os
from config import get_config
from models import Article, BlogCategory, RoleType, RecruitmentStage, Vacancy, Recruiter
from services import BlogService, CapacityService, FileService

# Load configuration based on environment
app = Flask(__name__)
app.config.from_object(get_config())

@app.after_request
def set_security_headers(response):
    """Apply security headers to all responses."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'

    if request.is_secure:
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

# Initialize CSRF Protection
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)

# Initialize Services
blog_service = BlogService(app.config['ARTICLES_DIR'])
capacity_service = CapacityService()
file_service = FileService(
    upload_extensions=app.config['UPLOAD_EXTENSIONS'],
    max_content_length=app.config['MAX_CONTENT_LENGTH']
)

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
BLOG_CATEGORIES = {}
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

PROJECTS = [
    {"id": "capacity-tracker", "name": "Recruitment Capacity Tracker", "description": "Calculate team capacity for recruitment workloads.", "status": "active", "url": "/projects/capacity-tracker"},
    {"id": "meal-generator", "name": "Meal Generator", "description": "A tool to help plan weekly meals.", "status": "planned"},
    {"id": "fm-tools", "name": "FM Analytics Tools", "description": "Utilities for analyzing FM save data.", "status": "planned"},
]

def format_date(date_string):
    """Format date string for Jinja templates."""
    date_obj = datetime.strptime(date_string, "%Y-%m-%d")
    return date_obj.strftime("%B %d, %Y")

# ========== JINJA TEMPLATE GLOBALS ==========

app.jinja_env.globals["format_date"] = format_date

@app.route("/")
def home():
    latest_article = blog_service.get_latest_article(BLOG_CATEGORIES)
    return render_template("index.html", latest_article=latest_article, categories=BLOG_CATEGORIES, projects=PROJECTS)

@app.route("/blog")
def blog_home():
    # Pass BlogCategory objects directly - they have article_count property
    categories = list(BLOG_CATEGORIES.values())
    return render_template("blog_home.html", categories=categories)

@app.route("/blog/<category_id>")
def blog_category(category_id):
    category = BLOG_CATEGORIES.get(category_id)
    if not category:
        abort(404)
    articles = blog_service.get_category_articles(category)
    return render_template("blog_category.html", category=category, articles=articles, total_parts=len(articles))

@app.route("/blog/<category_id>/<article_id>")
def article(category_id, article_id):
    category = BLOG_CATEGORIES.get(category_id)
    if not category:
        abort(404)

    article_data = category.get_article_by_id(article_id)
    if not article_data:
        abort(404)

    content = blog_service.get_article_content(article_data.filename)
    if not content:
        abort(404)

    prev_article, next_article = blog_service.get_prev_next_articles(category, article_data.part)
    content_blocks = blog_service.parse_content(content)
    reading_time = blog_service.calculate_reading_time(content)

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

@app.route("/article/<article_id>")
def article_legacy(article_id):
    for cat_id, category in BLOG_CATEGORIES.items():
        for article in category.articles:
            if article.id == article_id:
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
    POST: Process form data (manual or Excel upload) and display results
    """
    recruiters_data = []
    team_summary = None
    errors = []
    input_method = None

    if request.method == "POST":
        # Check if this is an Excel upload or manual input
        if 'excel_file' in request.files and request.files['excel_file'].filename:
            # Excel upload processing
            input_method = 'excel'
            file = request.files['excel_file']

            # Validate file using service
            is_valid, error_msg = file_service.validate_uploaded_file(file)
            if not is_valid:
                errors.append(error_msg)
            else:
                # Process Excel file using service
                recruiters_dict, excel_errors = file_service.process_excel_upload(file)
                errors.extend(excel_errors)

                # Calculate capacity for each recruiter using service
                if not errors:
                    for recruiter_name, vacancies in recruiters_dict.items():
                        try:
                            capacity_info = capacity_service.calculate_recruiter_capacity_from_vacancies(vacancies)
                            recruiter = {
                                'name': recruiter_name,
                                **capacity_info
                            }
                            recruiters_data.append(recruiter)
                        except Exception as e:
                            errors.append(f"Error calculating capacity for {recruiter_name}: {str(e)}")

        else:
            # Manual input processing
            input_method = 'manual'

            # Collect all vacancy data from form
            index = 0
            vacancies_by_recruiter = {}

            while f'recruiter_{index}' in request.form:
                recruiter_name = request.form.get(f'recruiter_{index}', '').strip()
                vacancy_name = request.form.get(f'vacancy_name_{index}', '').strip()
                role_type = request.form.get(f'role_type_{index}', '').strip().lower()
                internal_str = request.form.get(f'internal_{index}', 'no').strip().lower()
                stage = request.form.get(f'stage_{index}', '').strip().lower()

                # Skip if recruiter name is empty
                if not recruiter_name:
                    index += 1
                    continue

                # Validate role type
                if role_type not in ['easy', 'medium', 'hard']:
                    errors.append(f"Invalid role type for vacancy {index + 1}")
                    index += 1
                    continue

                # Parse internal
                is_internal = (internal_str == 'yes')

                # Default vacancy name if not provided
                if not vacancy_name:
                    vacancy_name = f"Vacancy {index + 1}"

                # Add to recruiter's vacancy list
                if recruiter_name not in vacancies_by_recruiter:
                    vacancies_by_recruiter[recruiter_name] = []

                vacancies_by_recruiter[recruiter_name].append({
                    'vacancy_name': vacancy_name,
                    'role_type': role_type,
                    'is_internal': is_internal,
                    'stage': stage
                })

                index += 1

            # Calculate capacity for each recruiter using service
            if not errors and vacancies_by_recruiter:
                for recruiter_name, vacancies in vacancies_by_recruiter.items():
                    try:
                        capacity_info = capacity_service.calculate_recruiter_capacity_from_vacancies(vacancies)
                        recruiter = {
                            'name': recruiter_name,
                            **capacity_info
                        }
                        recruiters_data.append(recruiter)
                    except Exception as e:
                        errors.append(f"Error calculating capacity for {recruiter_name}: {str(e)}")

        # Calculate team summary if we have data using service
        if recruiters_data:
            team_summary = capacity_service.calculate_team_summary(recruiters_data)

    return render_template(
        "projects/capacity_tracker.html",
        recruiters=recruiters_data,
        team_summary=team_summary,
        errors=errors,
        input_method=input_method
    )

@app.route("/projects/capacity-tracker/download-template")
def download_capacity_template():
    """
    Generate and download a sample Excel template for capacity tracker.
    """
    # Generate template using file service
    workbook = file_service.generate_capacity_template()

    # Save to BytesIO
    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='capacity_tracker_template.xlsx'
    )

@app.route("/about")
def about():
    return render_template("about.html")

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

if __name__ == "__main__":
    # Get configuration from app config (already loaded)
    debug_mode = app.config.get('DEBUG', False)
    env_name = os.environ.get('FLASK_ENV', 'development')

    # Display startup information
    print("=" * 60)
    print(f"Flask Application Starting")
    print(f"Environment: {env_name}")
    print(f"Debug Mode: {debug_mode}")
    print(f"Config: {app.config.__class__.__name__}")
    print("=" * 60)

    if debug_mode and env_name == 'production':
        print("\n⚠️  WARNING: Debug mode enabled in production!")
        print("This is a security risk. Set FLASK_DEBUG=false\n")

    # Get host and port from environment or use defaults
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', 5000))

    app.run(host=host, port=port, debug=debug_mode)
