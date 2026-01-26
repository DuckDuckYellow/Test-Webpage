# CLAUDE.md - AI Assistant Guide

This document provides comprehensive guidance for AI assistants working on Newton's Repository codebase. Read this file carefully before making any changes to understand the architecture, conventions, and workflows.

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture Patterns](#architecture-patterns)
3. [Directory Structure](#directory-structure)
4. [Key Services](#key-services)
5. [Models & Data Flow](#models--data-flow)
6. [Development Workflows](#development-workflows)
7. [Testing Strategy](#testing-strategy)
8. [Coding Conventions](#coding-conventions)
9. [Security Considerations](#security-considerations)
10. [Common Tasks](#common-tasks)

---

## Project Overview

**Name:** Newton's Repository
**Type:** Flask web application (blog + Football Manager tools)
**Live URL:** https://newtonsrepository.dev/
**Tech Stack:** Python 3, Flask, Pydantic, OpenPyXL, BeautifulSoup4, Bootstrap 5

### Core Features

1. **Blog System** - Football Manager save stories with series navigation
2. **Squad Audit Tracker** - Analyze FM squads with per-90 metrics, role evaluation, and value scoring
3. **Recruitment Capacity Tracker** - Calculate recruiter workload and team capacity

---

## Architecture Patterns

### Application Factory Pattern

The codebase uses Flask's Application Factory pattern for clean initialization and testing:

```python
# app.py
def create_app(config_class=None):
    app = Flask(__name__)
    app.config.from_object(config_class or get_config())
    csrf.init_app(app)
    limiter.init_app(app)
    register_blueprints(app)
    return app
```

**Benefits:**
- Clean separation of configuration
- Easy testing with different configs
- Multiple app instances possible

### Layered Architecture

```
HTTP Request → Route (Blueprint) → Service → Model → Response
              (HTTP/Validation)   (Business)  (Data)
```

**Rules:**
- Routes handle HTTP concerns only (request/response, validation)
- Services contain ALL business logic (pure functions preferred)
- Models represent data structures (immutable when possible)
- NO business logic in routes or templates

### Blueprint Organization

Routes are organized by domain:

- `main_bp` - Homepage, about page, general navigation
- `blog_bp` - Article listing, individual articles, categories
- `projects_bp` - Squad Audit Tracker, Capacity Tracker

**Location:** All blueprints are in `/routes/` and registered in `app.py:register_blueprints()`

### Dependency Injection

Services are initialized globally in `create_app()` and imported where needed:

```python
# app.py
blog_service = None
capacity_service = None

def create_app():
    global blog_service, capacity_service
    blog_service = BlogService(app.config['ARTICLES_DIR'])
    capacity_service = CapacityService()

# routes/projects.py
from app import capacity_service  # Import when needed
```

**Important:** This pattern avoids circular imports while maintaining testability.

---

## Directory Structure

```
Test-Webpage/
├── app.py                      # Application factory & initialization
├── config.py                   # Environment-specific configurations
├── extensions.py               # Flask extensions (CSRF, rate limiter)
├── requirements.txt            # Python dependencies
│
├── routes/                     # HTTP route handlers (blueprints)
│   ├── __init__.py            # Exports all blueprints
│   ├── main.py                # Homepage, about, general routes
│   ├── blog.py                # Blog/article routes
│   └── projects.py            # Squad Audit & Capacity Tracker routes
│
├── services/                   # Business logic layer
│   ├── blog_service.py        # Article management
│   ├── capacity_service.py    # Recruitment capacity calculations
│   ├── squad_audit_service.py # Squad analysis & recommendations
│   ├── player_evaluator_service.py  # Player role evaluation
│   ├── squad_analysis_manager.py    # Orchestrates squad analysis
│   ├── file_service.py        # File upload handling
│   ├── fm_parser.py           # Football Manager HTML parser (legacy)
│   ├── fm_parser_v2.py        # Football Manager HTML parser (new format)
│   ├── parser_factory.py      # Detects FM format & returns parser
│   └── league_baseline_generator.py # Parses wage exports & generates baselines
│
├── models/                     # Data structures (Pydantic/dataclasses)
│   ├── article.py             # Article, BlogCategory
│   ├── squad_audit.py         # Player, Squad, PlayerAnalysis, SquadAnalysisResult
│   ├── vacancy.py             # Vacancy, Recruiter, TeamSummary
│   ├── role_definitions.py    # RoleDefinition, role requirements
│   ├── league_baseline.py     # LeagueWageBaseline, LeagueBaselineCollection
│   └── constants.py           # PositionCategory, metrics mappings
│
├── schemas/                    # Input validation (Pydantic)
│   └── recruitment.py         # VacancySchema, RecruiterSchema
│
├── analyzers/                  # Analysis engines
│   ├── role_evaluator.py      # Evaluates player fit for tactical roles
│   └── role_recommendation_engine.py  # Recommends optimal roles
│
├── templates/                  # Jinja2 HTML templates
│   ├── base.html              # Base template (extends to all pages)
│   ├── index.html             # Homepage
│   ├── blog_home.html         # Blog category listing
│   ├── article.html           # Individual article view
│   └── projects/              # Project-specific templates
│       ├── squad_audit_tracker.html
│       ├── capacity_tracker.html
│       └── role_detail_modal.html
│
├── articles/                   # Article content (.txt files)
├── static/                     # Static assets (CSS, JS, images)
├── data/                       # Pre-computed data files
│   └── league_baselines.json  # League wage baselines (455 baselines, 134 divisions)
│
├── scripts/                    # CLI tools and utilities
│   └── generate_league_baselines.py  # Generate league baselines from wage export
│
├── tests/                      # Test suite
│   ├── conftest.py            # Shared pytest fixtures
│   ├── unit/                  # Unit tests (services, models)
│   ├── integration/           # Integration tests (routes, security)
│   └── fixtures/              # Test data files
│
└── utils/                      # Utility modules
    └── logger.py              # Logging configuration
```

---

## Key Services

### Service Responsibilities

| Service | File | Purpose | Key Methods |
|---------|------|---------|-------------|
| **BlogService** | `blog_service.py` | Manages article content | `get_categories()`, `get_article()`, `parse_content()` |
| **CapacityService** | `capacity_service.py` | Recruitment workload calculations | `calculate_vacancy_load()`, `get_recruiter_summary()`, `calculate_team_summary()` |
| **SquadAuditService** | `squad_audit_service.py` | Squad analysis & value scoring | `analyze_squad()`, `suggest_formations()`, `generate_best_xi()`, `suggest_formations_with_xi()`, `export_to_csv_data()` |
| **PlayerEvaluatorService** | `player_evaluator_service.py` | Player position & role evaluation | `get_position_category()`, `evaluate_roles()`, `get_normalized_metrics()` |
| **SquadAnalysisManager** | `squad_analysis_manager.py` | Orchestrates full analysis pipeline | `process_squad_upload()`, `get_analysis_from_session()`, `get_formation_suggestions_with_xi()` |
| **FileService** | `file_service.py` | File upload & validation | `validate_uploaded_file()`, `process_excel_upload()` |
| **ParserFactory** | `parser_factory.py` | Detects FM HTML format | `get_parser()` (returns V1 or V2 parser) |
| **FMHTMLParser** | `fm_parser.py` | Parses FM HTML (legacy format) | `parse_html()` |
| **FMHTMLParserV2** | `fm_parser_v2.py` | Parses FM HTML (new format) | `parse_html()` |
| **LeagueBaselineGenerator** | `league_baseline_generator.py` | Parses wage exports & generates baselines | `parse_wage_export_html()`, `generate_baselines()`, `calculate_gk_multiplier()` |

### Service Design Principles

1. **Stateless by default** - Use class methods or static methods where possible
2. **Pure functions** - Same input = same output, no side effects
3. **Explicit dependencies** - All inputs as parameters, no hidden state
4. **Type hints required** - Document inputs/outputs with type annotations
5. **Raise exceptions, don't return errors** - Use `ValueError` for business logic errors

**Example Service:**

```python
class CapacityService:
    @classmethod
    def calculate_vacancy_load(cls, vacancy: Vacancy) -> float:
        """Calculate capacity load for a single vacancy."""
        base_capacity = cls._get_base_capacity(vacancy.role_type)
        internal_multiplier = 0.25 if vacancy.is_internal else 1.0
        stage_multiplier = cls._get_stage_multiplier(vacancy.stage)
        return base_capacity * internal_multiplier * stage_multiplier
```

### League Baseline System

**Purpose:** Compare player wages against league-wide averages for their position/division.

**Data Source:** `wage_player_export.html` (61-column FM wage export with Division + Wage data)

**Storage:** `data/league_baselines.json` (pre-computed statistics)

**Key Features:**
- **Dual Value Scoring:** Players receive both squad-based and league-based value scores
- **GK Multiplier:** Auto-calculated from top 5 European leagues (Premier League, La Liga, Serie A, Bundesliga, Ligue 1)
- **Position Aggregation:** Positions with <30 players aggregate into broader groups (Defenders/Midfielders/Attackers)
- **Low Sample Warnings:** Divisions with <100 total players flagged with warnings
- **Value Comparison Indicator:** "League Bargain" badge for players with league value 30+ higher than squad value

**Data Flow:**
```
1. wage_player_export.html (FM export)
   ↓
2. scripts/generate_league_baselines.py (CLI tool)
   ↓
3. LeagueBaselineGenerator.parse_wage_export_html()
   ↓
4. LeagueBaselineGenerator.generate_baselines()
   ↓
5. data/league_baselines.json (455 baselines, 134 divisions, GK multiplier: 0.677)
   ↓
6. App startup → initialize_league_baselines() loads JSON
   ↓
7. User selects division during squad upload
   ↓
8. SquadAuditService calculates league_value_score for each player
   ↓
9. Template displays both squad and league values side-by-side
```

**Regenerating Baselines:**
```bash
python scripts/generate_league_baselines.py wage_player_export.html
```

**Lookup Logic (Cascade):**
1. Try specific position (e.g., FB)
2. If not found or <30 players → try aggregated group (e.g., Defenders)
3. If GK and no baseline → estimate using `avg_outfield_wage × gk_multiplier`
4. Return None if no match

**Key Models:**
- `LeagueWageBaseline` - Single baseline (division + position + wage stats)
- `LeagueBaselineCollection` - Collection with O(1) lookup cache

### Best XI System

**Purpose:** Generate optimal starting XI and bench for each recommended formation based on role evaluation data.

**Key Features:**
- **Greedy Assignment Algorithm:** Fills positions by scarcity order to avoid "wasting" versatile players on common positions
- **Role-Based Scoring:** Uses role evaluation verdicts (ELITE=4, GOOD=3, AVERAGE=2, POOR=1) with natural position bonuses
- **Balanced Bench Selection:** Enforces minimum coverage (1 GK, 2 DEF, 1 MID, 2 AM, 1 ST) before filling remaining slots
- **Recruitment Warnings:** Shows dashed red borders for unfilled mandatory bench positions
- **Drag-and-Drop Swapping:** Users can swap players between XI and bench with automatic score recalculation
- **Pitch Visualization:** Formation-specific player positioning with percentage-based coordinates

**Algorithm Flow:**
```
1. Get formation requirements (e.g., 4-3-3: 1 GK, 2 CB, 2 FB, 3 CM, 3 ST/W)
   ↓
2. Order positions by scarcity (fewer available players = higher priority)
   ↓
3. For each position, find best available player using role evaluation scores
   ↓
4. Assign player, mark as used, continue to next position
   ↓
5. Generate bench with Phase 1 (minimum coverage) + Phase 2 (best remaining)
   ↓
6. Calculate total quality score (sum of all XI player scores)
   ↓
7. Return FormationXI with XI, bench, gaps, and score
```

**Position-to-Roles Mapping:**
```python
POSITION_TO_ROLES = {
    GK: ['GK'],
    CB: ['CB-STOPPER', 'BCB'],
    FB: ['FB', 'WB'],
    DM: ['MD'],
    CM: ['MC', 'MD'],
    AM: ['AM(C)'],
    W: ['WAP', 'WAS'],
    ST: ['ST-GS', 'ST-PROVIDER']
}
```

**Key Models:**
- `PlayerAssignment` - Player with assigned position, role, and score
- `FormationXI` - Complete XI with bench, gaps, and pitch layout coordinates
- `BenchGap` - Represents unfilled mandatory bench position

**UI Features:**
- Pitch visualization with formation-specific layouts (stored as x,y coordinates 0-100)
- Drag-and-drop between XI and bench positions
- Quality score badge with flash animation on swap
- Verdict-colored badges (green=ELITE, blue=GOOD, yellow=AVERAGE, red=POOR)

---

## Models & Data Flow

### Data Models (`/models/`)

All models use Python `@dataclass` for immutability and clarity:

```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Player:
    """Represents a football player with statistics."""
    name: str
    position: str
    age: int
    wage: float
    apps: int
    mins: int
    # Per-90 statistics
    av_rat: float
    xg: float
    xa: float
    # ... additional stats
```

**Key Models:**

| Model | Purpose | Location |
|-------|---------|----------|
| `Article` | Blog article metadata | `models/article.py` |
| `BlogCategory` | Article category/series | `models/article.py` |
| `Player` | FM player with stats | `models/squad_audit.py` |
| `Squad` | Collection of players | `models/squad_audit.py` |
| `PlayerAnalysis` | Analysis results for one player | `models/squad_audit.py` |
| `SquadAnalysisResult` | Complete squad analysis | `models/squad_audit.py` |
| `Vacancy` | Recruitment position | `models/vacancy.py` |
| `Recruiter` | Recruiter with vacancies | `models/vacancy.py` |
| `LeagueWageBaseline` | League wage baseline for division/position | `models/league_baseline.py` |
| `LeagueBaselineCollection` | Collection of baselines with lookup cache | `models/league_baseline.py` |
| `PlayerAssignment` | Player assigned to a position/role in Best XI | `models/squad_audit.py` |
| `FormationXI` | Best XI selection with bench and quality score | `models/squad_audit.py` |
| `BenchGap` | Missing mandatory bench position (recruitment warning) | `models/squad_audit.py` |

### Validation Schemas (`/schemas/`)

Pydantic schemas validate user input BEFORE processing:

```python
from pydantic import BaseModel, validator

class VacancySchema(BaseModel):
    name: str
    role_type: str
    is_internal: bool
    stage: Optional[str] = None

    @validator('role_type')
    def validate_role_type(cls, v):
        if v not in ['easy', 'medium', 'hard']:
            raise ValueError(f"Invalid role type: {v}")
        return v
```

**Pattern:** Raw input → Pydantic schema → Validated dict → Model/Service

### Data Flow Example: Squad Audit

```
1. User uploads HTML file
   ↓
2. FileService validates file (extension, size)
   ↓
3. ParserFactory detects format (V1/V2)
   ↓
4. FMHTMLParserV2 parses → Squad object
   ↓
5. PlayerEvaluatorService evaluates roles for each player
   ↓
6. SquadAuditService analyzes squad → SquadAnalysisResult
   ↓
7. Result stored in temp file with UUID
   ↓
8. Session stores UUID for retrieval
   ↓
9. Template renders results
```

---

## Development Workflows

### Environment Setup

```bash
# 1. Clone repository
git clone https://github.com/DuckDuckYellow/Test-Webpage.git
cd Test-Webpage

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file (copy from .env.example)
cp .env.example .env
# Generate SECRET_KEY:
python -c 'import secrets; print(secrets.token_hex(32))'

# 5. Run development server
python app.py
```

### Configuration

Three environments with different configs:

| Environment | Config Class | Use Case |
|-------------|--------------|----------|
| `development` | `DevelopmentConfig` | Local development (DEBUG=True, HTTP allowed) |
| `production` | `ProductionConfig` | Live deployment (DEBUG=False, HTTPS required) |
| `testing` | `TestingConfig` | Pytest runs (CSRF disabled, smaller file limits) |

**Set environment:**

```bash
export FLASK_ENV=development  # or production, testing
```

**Required environment variables:**

- `SECRET_KEY` - Session encryption key (REQUIRED in all environments)
- `FLASK_ENV` - Environment name (defaults to `development`)
- `MAX_UPLOAD_SIZE` - Max file upload size in bytes (defaults to 10MB)

### Adding New Features

**General workflow:**

1. **Create model** - Define data structure in `/models/`
2. **Create service** - Implement business logic in `/services/`
3. **Add route** - Create endpoint in appropriate blueprint in `/routes/`
4. **Create template** - Add HTML template in `/templates/`
5. **Write tests** - Add unit tests in `/tests/unit/`, integration tests in `/tests/integration/`
6. **Update documentation** - Update this CLAUDE.md if patterns change

**Example: Adding a new project tool**

1. Create model: `/models/my_feature.py`
   ```python
   @dataclass
   class MyFeatureResult:
       data: List[dict]
       summary: str
   ```

2. Create service: `/services/my_feature_service.py`
   ```python
   class MyFeatureService:
       @classmethod
       def process_data(cls, input_data: dict) -> MyFeatureResult:
           # Business logic here
           pass
   ```

3. Add route: `/routes/projects.py`
   ```python
   @projects_bp.route('/my-feature', methods=['GET', 'POST'])
   def my_feature():
       from app import my_feature_service
       # Handle request
   ```

4. Create template: `/templates/projects/my_feature.html`
   ```html
   {% extends "base.html" %}
   {% block content %}
       <!-- Feature UI -->
   {% endblock %}
   ```

5. Register in app: `/app.py`
   ```python
   def initialize_projects():
       PROJECTS.extend([{
           "id": "my-feature",
           "name": "My Feature",
           "description": "Description",
           "status": "active",
           "url": "/projects/my-feature"
       }])
   ```

### Adding Blog Articles

1. **Create content file:** `/articles/article7.txt`
   - Use blank lines to separate paragraphs
   - Short lines (< 80 chars) without periods become headings

2. **Register article:** Edit `app.py:initialize_blog_categories()`
   ```python
   "articles": [
       {
           "id": "my-article-slug",
           "title": "Article Title",
           "date": "2024-07-15",
           "filename": "article7.txt",
           "part": 7
       },
   ]
   ```

3. **Restart app** - Articles load on startup

---

## Testing Strategy

### Test Structure

```
tests/
├── conftest.py                    # Shared fixtures
├── test_squad_audit_end_to_end.py # Full pipeline tests
├── test_role_evaluation.py        # Role analysis tests
├── unit/                          # Unit tests (isolated components)
│   ├── test_capacity.py           # Capacity calculations
│   ├── test_models.py             # Model instantiation
│   ├── test_fm_parser.py          # HTML parsing
│   ├── test_squad_audit.py        # Squad analysis
│   └── test_blog.py               # Blog service
├── integration/                   # Integration tests (multiple components)
│   ├── test_routes.py             # HTTP endpoints
│   └── test_security.py           # Security headers
└── fixtures/                      # Test data files
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_capacity.py

# Run with coverage
pytest --cov=services --cov=models

# Run specific test class
pytest tests/unit/test_capacity.py::TestEasyRoles

# Run with verbose output
pytest -v

# Run and stop on first failure
pytest -x
```

### Writing Tests

**Unit test pattern:**

```python
# tests/unit/test_my_service.py
import pytest
from services.my_service import MyService
from models.my_model import MyModel

class TestMyService:
    """Test MyService functionality."""

    def test_basic_calculation(self, my_service):
        """Test basic calculation logic."""
        input_data = {"value": 10}
        result = my_service.process(input_data)
        assert result.total == 10

    def test_invalid_input_raises_error(self, my_service):
        """Test that invalid input raises ValueError."""
        with pytest.raises(ValueError, match="Invalid value"):
            my_service.process({"value": -1})
```

**Integration test pattern:**

```python
# tests/integration/test_routes.py
def test_my_feature_endpoint(client):
    """Test /my-feature endpoint returns 200."""
    response = client.get('/projects/my-feature')
    assert response.status_code == 200
    assert b'Expected Content' in response.data
```

### Fixtures (conftest.py)

Common fixtures available in all tests:

- `app` - Flask test application with TestingConfig
- `client` - Flask test client for HTTP requests
- `capacity_service` - CapacityService instance
- `squad_audit_service` - SquadAuditService instance
- `sample_player` - Pre-built Player object
- `sample_squad` - Pre-built Squad object

**Using fixtures:**

```python
def test_with_fixtures(client, capacity_service, sample_player):
    """Fixtures are injected automatically by pytest."""
    # Use fixtures directly
    pass
```

---

## Coding Conventions

### Naming Conventions

| Element | Pattern | Example |
|---------|---------|---------|
| Services | `{Feature}Service` | `CapacityService`, `SquadAuditService` |
| Managers | `{Feature}Manager` | `SquadAnalysisManager` |
| Blueprints | `{domain}_bp` | `projects_bp`, `blog_bp` |
| Routes/Functions | `snake_case` | `squad_audit_tracker()`, `get_position_category()` |
| Classes | `PascalCase` | `Player`, `Squad`, `SquadAnalysisResult` |
| Constants | `UPPER_SNAKE_CASE` | `POSITION_METRICS`, `BLOG_CATEGORIES` |
| Private methods | `_snake_case` | `_get_base_capacity()`, `_parse_player_row()` |

### Import Organization

```python
# 1. Standard library imports
import os
from pathlib import Path
from typing import List, Optional

# 2. Third-party imports
from flask import Flask, request, jsonify
from pydantic import BaseModel

# 3. Local application imports
from models import Player, Squad
from services import SquadAuditService
```

**Avoiding circular imports:**

- Routes import from `app` module (global services)
- Services import from `models` only (leaf dependencies)
- Models have NO imports from `app` or `services`

### Type Hints

**Required for all function signatures:**

```python
def analyze_squad(self, squad: Squad) -> SquadAnalysisResult:
    """Analyze squad and return results."""
    pass

def calculate_vacancy_load(cls, vacancy: Vacancy) -> float:
    """Calculate capacity load percentage."""
    pass
```

### Error Handling

**Services raise exceptions:**

```python
if not squad.players:
    raise ValueError("Squad must have at least one player")
```

**Routes catch and format for users:**

```python
try:
    result = squad_audit_service.analyze_squad(squad)
except ValueError as e:
    flash(f"Error: {str(e)}", "danger")
    return redirect(url_for('projects.squad_audit_tracker'))
```

**Logging for debugging:**

```python
from flask import current_app

current_app.logger.error(f"Analysis failed: {e}")
current_app.logger.info(f"Processing squad with {len(squad.players)} players")
```

### Code Style

- **Line length:** Max 120 characters (prefer 80-100)
- **Docstrings:** Google style for functions/classes
- **Comments:** Explain "why", not "what" (code should be self-documenting)
- **Composition over inheritance:** Prefer composing services over subclassing
- **Immutability:** Use `@dataclass(frozen=True)` for models where possible

**Example docstring:**

```python
def calculate_vacancy_load(cls, vacancy: Vacancy) -> float:
    """
    Calculate capacity load percentage for a vacancy.

    Formula: Base × Internal_Multiplier × Stage_Multiplier
    - Easy: 1/30 = 3.33%
    - Medium: 1/20 = 5%
    - Hard: 1/12 = 8.33%
    - Internal roles: 0.25× multiplier

    Args:
        vacancy: Vacancy object with role_type, is_internal, stage

    Returns:
        Capacity load as decimal (e.g., 0.05 = 5%)

    Raises:
        ValueError: If role_type is invalid
    """
```

---

## Security Considerations

### Security Headers

All responses include security headers (configured in `app.py`):

```python
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' ...
Strict-Transport-Security: max-age=31536000; includeSubDomains (HTTPS only)
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
```

**Do NOT remove or weaken these headers without explicit approval.**

### CSRF Protection

CSRF tokens required for all POST/PUT/DELETE requests:

```html
<form method="POST">
    {{ csrf_token() }}
    <!-- Form fields -->
</form>
```

**AJAX requests:**

```javascript
fetch('/api/endpoint', {
    method: 'POST',
    headers: {
        'X-CSRFToken': document.querySelector('[name=csrf_token]').value
    },
    body: JSON.stringify(data)
})
```

**Exempting routes (use sparingly):**

```python
from flask_wtf.csrf import csrf

@projects_bp.route('/public-api', methods=['POST'])
@csrf.exempt
def public_api():
    # Only exempt if absolutely necessary
    pass
```

### Rate Limiting

Projects blueprint is rate-limited to prevent abuse:

```python
# app.py
limiter.limit("10 per minute")(projects_bp)
```

**Custom rate limits:**

```python
from extensions import limiter

@projects_bp.route('/expensive-operation')
@limiter.limit("5 per hour")
def expensive_operation():
    pass
```

### File Upload Security

File uploads are validated for:

1. **Extension whitelist:** Only `.xlsx`, `.xls` allowed (configured in `config.py`)
2. **Size limit:** 10MB default (configurable via `MAX_CONTENT_LENGTH`)
3. **Content validation:** Files parsed to ensure valid structure

**FileService handles validation:**

```python
file_service.validate_uploaded_file(file)  # Raises ValueError if invalid
```

### Session Security

- `SESSION_COOKIE_HTTPONLY = True` - Prevents JavaScript access
- `SESSION_COOKIE_SAMESITE = 'Lax'` - CSRF protection
- `SESSION_COOKIE_SECURE = True` (production) - HTTPS only
- Session timeout: 1 hour

### Input Validation

**All user input validated with Pydantic schemas:**

```python
try:
    validated = VacancySchema(**raw_input)
except ValidationError as e:
    return jsonify({"error": str(e)}), 400
```

**Never trust user input - always validate at the boundary.**

---

## Common Tasks

### Task: Add a new service method

1. **Write the service method:**

```python
# services/my_service.py
class MyService:
    @classmethod
    def new_calculation(cls, input_value: int) -> float:
        """Calculate something useful."""
        if input_value < 0:
            raise ValueError("Input must be non-negative")
        return input_value * 1.5
```

2. **Write tests first (TDD):**

```python
# tests/unit/test_my_service.py
def test_new_calculation(my_service):
    result = my_service.new_calculation(10)
    assert result == 15.0

def test_new_calculation_invalid_input(my_service):
    with pytest.raises(ValueError):
        my_service.new_calculation(-1)
```

3. **Run tests:**

```bash
pytest tests/unit/test_my_service.py -v
```

### Task: Add a new route

1. **Choose appropriate blueprint:**

```python
# routes/projects.py for project features
# routes/blog.py for blog features
# routes/main.py for general pages
```

2. **Add route handler:**

```python
@projects_bp.route('/new-feature', methods=['GET', 'POST'])
def new_feature():
    """Handle new feature requests."""
    if request.method == 'POST':
        # Process form data
        from app import my_service
        result = my_service.process(request.form)
        return render_template('projects/new_feature.html', result=result)
    return render_template('projects/new_feature.html')
```

3. **Create template:**

```html
<!-- templates/projects/new_feature.html -->
{% extends "base.html" %}

{% block content %}
<h1>New Feature</h1>
<form method="POST">
    {{ csrf_token() }}
    <!-- Form fields -->
    <button type="submit">Submit</button>
</form>
{% endblock %}
```

4. **Add integration test:**

```python
def test_new_feature_route(client):
    response = client.get('/projects/new-feature')
    assert response.status_code == 200
```

### Task: Debug a production issue

1. **Check logs:**

```bash
# Application logs (if configured with file handler)
tail -f logs/app.log

# Server logs (gunicorn/nginx)
tail -f /var/log/nginx/error.log
```

2. **Reproduce locally:**

```bash
# Set production config
export FLASK_ENV=production
export SECRET_KEY=<production-key>
python app.py
```

3. **Add debug logging:**

```python
from flask import current_app

current_app.logger.debug(f"Processing input: {input_data}")
current_app.logger.info(f"Result: {result}")
current_app.logger.error(f"Error occurred: {e}", exc_info=True)
```

4. **Use pytest for reproduction:**

```python
def test_production_issue():
    """Reproduce production issue for debugging."""
    # Set up exact conditions from production
    # Add assertions to verify fix
```

### Task: Deploy new changes

1. **Run full test suite:**

```bash
pytest
```

2. **Check for security issues:**

```bash
# Run security tests
pytest tests/integration/test_security.py -v
```

3. **Update version/changelog (if applicable)**

4. **Commit and push:**

```bash
git add .
git commit -m "feat: Add new feature X

- Implemented Y
- Updated Z
- Added tests for W"
git push origin main
```

5. **Deploy to production:**

```bash
# Pull changes on server
git pull origin main

# Restart gunicorn
sudo systemctl restart gunicorn

# Check status
sudo systemctl status gunicorn
```

### Task: Optimize performance

**Common bottlenecks:**

1. **N+1 queries** - Not applicable (no database ORM)
2. **Large file processing** - Use streaming/chunking for FM HTML parsing
3. **Session storage** - Already using temp files + UUIDs for large data
4. **Template rendering** - Cache static content, minimize loops in templates

**Profiling:**

```python
import cProfile
import pstats

def profile_function():
    profiler = cProfile.Profile()
    profiler.enable()

    # Function to profile
    result = my_service.expensive_operation(data)

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)
```

---

## Additional Resources

### Related Documentation

- [README.md](README.md) - Project setup and overview
- [TODO.md](TODO.md) - Current development priorities
- [CAPACITY_TRACKER_V2_GUIDE.md](CAPACITY_TRACKER_V2_GUIDE.md) - Capacity Tracker feature guide
- [REFACTORING_ASSESSMENT.md](REFACTORING_ASSESSMENT.md) - Architecture decision records
- [SECURITY_FIXES_SUMMARY.md](SECURITY_FIXES_SUMMARY.md) - Security improvements history

### External Documentation

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Bootstrap 5 Documentation](https://getbootstrap.com/docs/5.0/)

### Key Files to Reference

When making changes, consult these files for examples:

- **Service patterns:** `services/capacity_service.py` (clean service design)
- **Route patterns:** `routes/projects.py` (comprehensive route handling)
- **Model patterns:** `models/squad_audit.py` (dataclass usage)
- **Test patterns:** `tests/unit/test_capacity.py` (extensive test coverage)
- **Template patterns:** `templates/projects/squad_audit_tracker.html` (Bootstrap forms)

---

## Contributing Guidelines

When working on this codebase:

1. **Read this document first** - Understand patterns before making changes
2. **Follow existing patterns** - Maintain consistency with current architecture
3. **Write tests** - All new features need unit tests minimum
4. **Type hints required** - All functions need proper type annotations
5. **Document complex logic** - Add docstrings for non-obvious code
6. **Security first** - Never weaken security headers or validation
7. **Keep services pure** - Business logic stays in services, not routes
8. **Don't over-engineer** - Solve the current problem, not hypothetical future ones
9. **Test before committing** - Run `pytest` to verify nothing broke
10. **Ask questions** - Better to clarify than assume

---

## Frequently Asked Questions

### Q: Where do I put business logic?

**A:** Always in services (`/services/`). Routes should only handle HTTP concerns (validation, response formatting).

### Q: Should I use Pydantic or dataclass?

**A:**
- **Pydantic** - For input validation (user forms, API requests)
- **Dataclass** - For internal data models (Player, Squad, etc.)

### Q: How do I access services in routes?

**A:**

```python
from app import capacity_service, squad_audit_service, file_service
```

### Q: Where do I add new constants?

**A:** `/models/constants.py` for domain constants, `config.py` for configuration

### Q: How do I test routes that require authentication?

**A:** This app doesn't have authentication yet. For future: create fixtures that log in test users.

### Q: Can I add new dependencies?

**A:** Yes, but:
1. Justify the need (don't add for trivial features)
2. Update `requirements.txt`
3. Document usage in this file
4. Ensure compatible licenses

### Q: How do I handle large file uploads?

**A:** Use temp files + UUIDs (see `SquadAnalysisManager` pattern). Never store large data in sessions.

### Q: Should I use SQLAlchemy or keep plain text/CSV?

**A:** Current architecture uses plain text for simplicity. Only migrate to database if:
- Need complex queries
- Multi-user concurrent writes
- Data volume exceeds memory capacity

### Q: How do I add client-side validation?

**A:** Use Bootstrap 5 form validation classes + custom JavaScript. Always validate server-side too (never trust client).

---

**Last Updated:** 2026-01-26
**Maintainer:** DuckDuckYellow
**AI Assistant Version:** Claude Code (Anthropic)
