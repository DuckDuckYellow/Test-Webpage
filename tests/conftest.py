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


@pytest.fixture
def squad_audit_service():
    """
    SquadAuditService instance for testing squad analysis.

    Imports the actual service to ensure tests validate real code.
    """
    from services.squad_audit_service import SquadAuditService
    return SquadAuditService()


@pytest.fixture
def fm_parser():
    """
    FMHTMLParser instance for testing FM HTML parsing.
    """
    from services.fm_parser import FMHTMLParser
    return FMHTMLParser()


@pytest.fixture
def sample_player():
    """Sample Player model for testing."""
    from models import Player

    return Player(
        name='Josh Bowler',
        position_selected='AMR',
        position='AM (RL), ST (C)',
        age=29,
        wage=26000.0,
        apps=1,
        subs=3,
        gls=0,
        ast=1,
        av_rat=7.30,
        expires='30/6/2031',
        inf='PR',
        # Per-90 statistics
        int_90=None,
        xg=None,
        shot_90=3.39,
        ch_c_90=0.97,
        drb_90=6.00,
        blk_90=0.48,
        k_tck_90=0.00,
        hdr_pct=None,
        tck_r=None,
        pas_pct=None,
        con_90=None,
        xgp=None,
        sv_pct=None
    )


@pytest.fixture
def sample_elite_player():
    """Sample elite-performing player for testing."""
    from models import Player

    return Player(
        name='Damián Pizarro',
        position_selected='STC',
        position='ST (C)',
        age=23,
        wage=55000.0,
        apps=13,
        subs=3,
        gls=7,
        ast=1,
        av_rat=7.01,
        expires='30/6/2033',
        inf='',
        int_90=0.90,
        xg=6.84,
        shot_90=2.78,
        ch_c_90=0.08,
        drb_90=1.55,
        blk_90=0.08,
        k_tck_90=0.00,
        hdr_pct=35.0,
        tck_r=81.0,
        pas_pct=84.0,
        con_90=None,
        xgp=None,
        sv_pct=None
    )


@pytest.fixture
def sample_goalkeeper():
    """Sample goalkeeper for testing."""
    from models import Player

    return Player(
        name='Alban Lafont',
        position_selected='GK',
        position='GK',
        age=29,
        wage=29000.0,
        apps=18,
        subs=0,
        gls=0,
        ast=0,
        av_rat=6.84,
        expires='30/6/2032',
        inf='',
        int_90=0.11,
        xg=0.00,
        shot_90=None,
        ch_c_90=None,
        drb_90=None,
        blk_90=None,
        k_tck_90=0.06,
        hdr_pct=None,
        tck_r=None,
        pas_pct=95.0,
        con_90=1.50,
        xgp=-6.33,
        sv_pct=56.0
    )


@pytest.fixture
def sample_squad(sample_player, sample_elite_player, sample_goalkeeper):
    """Sample Squad with multiple players for testing."""
    from models import Squad, Player

    # Create additional players for a realistic squad
    cb_player = Player(
        name='Giovanni Leoni',
        position_selected='DCR',
        position='D (C)',
        age=21,
        wage=23000.0,
        apps=9,
        subs=4,
        gls=1,
        ast=0,
        av_rat=6.96,
        expires='30/6/2031',
        inf='',
        int_90=2.04,
        xg=0.35,
        shot_90=0.21,
        ch_c_90=None,
        drb_90=None,
        blk_90=0.11,
        k_tck_90=0.21,
        hdr_pct=80.0,
        tck_r=77.0,
        pas_pct=94.0,
        con_90=None,
        xgp=None,
        sv_pct=None
    )

    fb_player = Player(
        name='Marc Pubill',
        position_selected='DR',
        position='D/WB (R)',
        age=25,
        wage=32500.0,
        apps=16,
        subs=2,
        gls=2,
        ast=2,
        av_rat=7.03,
        expires='30/6/2033',
        inf='Yel',
        int_90=3.28,
        xg=0.64,
        shot_90=0.55,
        ch_c_90=0.41,
        drb_90=1.50,
        blk_90=0.75,
        k_tck_90=0.14,
        hdr_pct=66.0,
        tck_r=88.0,
        pas_pct=84.0,
        con_90=None,
        xgp=None,
        sv_pct=None
    )

    players = [
        sample_goalkeeper,
        cb_player,
        fb_player,
        sample_elite_player,
        sample_player
    ]

    return Squad(players=players)
