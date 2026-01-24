# Newton's Repository - Football Manager Blog & Projects

A personal website featuring Football Manager save stories and useful tools. Built with Python and Flask with enterprise-grade architecture.

**Status:** Live at [newtonsrepository.dev](https://newtonsrepository.dev/)

## Tech Stack

- **Backend:** Python 3, Flask, Pydantic (validation), OpenPyXL, BeautifulSoup4
- **Frontend:** HTML5, CSS3, Bootstrap 5
- **Templating:** Jinja2
- **Testing:** Pytest
- **Storage:** Plain text files (blog), In-memory/CSV (projects)

## Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/DuckDuckYellow/Test-Webpage.git
cd Test-Webpage
```

### 2. Create virtual environment

```bash
python -m venv venv

# Activate on Mac/Linux:
source venv/bin/activate

# Activate on Windows:
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
python app.py
```

### 5. Access in browser

Open [https://newtonsrepository.dev/](https://newtonsrepository.dev/)

## Project Structure

```
Test-Webpage/
├── app.py              # Application factory
├── config.py           # Configuration management
├── extensions.py       # Flask extensions
├── requirements.txt    # Python dependencies
├── README.md           # This file
├── routes/             # Blueprint definitions
├── services/           # Business logic layer
├── models/             # Data models (Pydantic/Dataclasses)
├── analyzers/          # Analysis engines
├── templates/          # Jinja2 HTML templates
│   ├── base.html       # Base template
│   ├── projects/       # Project-specific templates
│   └── ...
└── articles/           # Article content
```

## Features

- **Article listing** with part badges, reading time, and excerpt previews
- **Individual article pages** with proper paragraph formatting
- **Series navigation** with Previous/Next Part buttons
- **Reading time estimates** calculated at ~200 words per minute
- **Section heading detection** automatically formats headings as h2 tags
- **Mobile responsive design** using Bootstrap 5
- **Clean typography** with comfortable line-height for readability
- **Custom 404 page** with navigation back to content

## Projects

### Squad Audit Tracker
Advanced tool for analyzing Football Manager squads:
- **Per-90 Metrics**: Normalized performance analysis across 8 position groups.
- **Role Evaluation**: Automatically evaluates players against 12 tactical roles (e.g., Ball Playing Defender, Mezzala).
- **Role Recommendations**: Suggests optimal role changes based on player attributes and performance.
- **Dual Value Scoring**:
  - **Squad-Based Value**: Performance relative to squad average wage
  - **League-Based Value**: Performance relative to league average wage (optional, 134 divisions)
- **Division Selection**: Compare wages against 50+ global divisions
- **Value Insights**: "League Bargain" indicator for players underpaid vs market value
- **League Percentiles**: See where players rank in league wage distribution

### Recruitment Capacity Tracker
Resource planning tool for recruitment teams:
- **Workload Analysis**: Calculates recruiter capacity based on vacancy types.
- **Excel Integration**: Supports bulk upload via Excel templates.
- **Team Summary**: Aggregates team-wide capacity metrics.

## How to Add New Articles

### Step 1: Create the text file

Add a new file in the `articles/` folder (e.g., `article7.txt`). Write your content with:
- Paragraphs separated by blank lines
- Section headings on their own line (detected automatically)

### Step 2: Register the article

In `app.py`, add an entry to the `ARTICLES` list:

```python
{
    "id": "your-url-slug",           # Used in URL: /article/your-url-slug
    "title": "Your Article Title",   # Displayed as h1
    "date": "2024-07-15",            # YYYY-MM-DD format
    "filename": "article7.txt",      # Matches your text file
    "part": 7                        # Part number in series
},
```

The article will automatically appear on the homepage with calculated reading time and excerpt.

## How Routing Works

| URL | Route | Description |
|-----|-------|-------------|
| `/` | `home()` | Lists all articles sorted by part number |
| `/article/<id>` | `article(id)` | Displays single article with navigation |
| `/about` | `about()` | Static about page |

## Developer Notes

### Dependencies

- **Flask** - Web framework. Only dependency needed for this project.

### Content Parsing

The `parse_content()` function in `app.py` detects headings using these patterns:
- Lines starting with "Part X"
- Short lines (<80 chars) without ending periods
- ALL CAPS lines

### Template Inheritance

All pages extend `base.html`, which contains:
- Bootstrap 5 CDN links
- Navigation bar
- Footer
- Custom CSS in `<style>` block

### Reading Time Calculation

`calculate_reading_time()` uses word count / 200, with minimum of 1 minute.

## License

Personal project - feel free to use as a template for your own blog.
