"""
Pytest Configuration and Fixtures

Provides shared fixtures for testing the Flask application using the
application factory pattern with clean, isolated test instances.
"""

import pytest
import os
from pathlib import Path


@pytest.fixture(scope='session')
def test_config():
    """Test configuration class."""
    from config import TestingConfig
    return TestingConfig


@pytest.fixture
def app(test_config):
    """
    Create and configure a Flask application instance for testing.

    Uses the application factory pattern to create a clean instance
    for each test function.
    """
    # Set test environment variables
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['SECRET_KEY'] = 'test-secret-key-for-pytest'

    from app import create_app
    app = create_app(test_config)

    # Push application context
    ctx = app.app_context()
    ctx.push()

    yield app

    # Clean up
    ctx.pop()


@pytest.fixture
def client(app):
    """
    Flask test client for making HTTP requests.

    Provides a test client that can make requests to the application
    without running a live server.
    """
    return app.test_client()


@pytest.fixture
def runner(app):
    """
    Flask CLI test runner.

    Provides a runner for testing CLI commands.
    """
    return app.test_cli_runner()


@pytest.fixture
def blog_service():
    """
    BlogService instance for testing blog-related functionality.

    Imports the actual service from the application to ensure
    tests validate real code, not reimplementations.
    """
    from app import blog_service
    return blog_service


@pytest.fixture
def capacity_service():
    """
    CapacityService instance for testing capacity calculations.

    Imports the actual service from the application to ensure
    tests validate real code, not reimplementations.
    """
    from services import CapacityService
    return CapacityService


@pytest.fixture
def file_service():
    """
    FileService instance for testing file operations.

    Imports the actual service from the application.
    """
    from app import file_service
    return file_service


@pytest.fixture
def sample_article():
    """Sample Article model for testing."""
    from models import Article
    return Article(
        id='test-article',
        title='Test Article',
        date='2024-01-15',
        filename='test.txt',
        part=1,
        category_id='test-category'
    )


@pytest.fixture
def sample_category():
    """Sample BlogCategory model for testing."""
    from models import BlogCategory, Article

    articles = [
        Article(id='article-1', title='Article 1', date='2024-01-15', filename='test1.txt', part=1),
        Article(id='article-2', title='Article 2', date='2024-02-20', filename='test2.txt', part=2),
    ]

    return BlogCategory(
        id='test-category',
        name='Test Category',
        subtitle='Test Subtitle',
        description='Test Description',
        image='test.png',
        articles=articles
    )


@pytest.fixture
def sample_vacancy():
    """Sample Vacancy model for testing."""
    from models import Vacancy, RoleType, RecruitmentStage

    return Vacancy(
        name='Senior Developer',
        role_type=RoleType.HARD,
        is_internal=False,
        stage=RecruitmentStage.SCREENING
    )


@pytest.fixture
def sample_recruiter():
    """Sample Recruiter model with vacancies for testing."""
    from models import Recruiter, Vacancy, RoleType, RecruitmentStage

    vacancies = [
        Vacancy(name='Role 1', role_type=RoleType.EASY, is_internal=False, stage=RecruitmentStage.SOURCING),
        Vacancy(name='Role 2', role_type=RoleType.MEDIUM, is_internal=True, stage=RecruitmentStage.SCREENING),
    ]

    return Recruiter(name='Test Recruiter', vacancies=vacancies)
