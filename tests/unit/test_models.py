"""
Unit Tests for Data Models

Tests the Article, BlogCategory, Vacancy, and Recruiter models.
"""

import pytest
from datetime import datetime
from models import Article, BlogCategory, Vacancy, Recruiter, RoleType, RecruitmentStage


class TestArticleModel:
    """Test Article dataclass."""

    def test_article_creation(self):
        """Test: Create article with required fields."""
        article = Article(
            id='test-article',
            title='Test Title',
            date='2024-01-15',
            filename='test.txt',
            part=1
        )

        assert article.id == 'test-article'
        assert article.title == 'Test Title'
        assert article.date == '2024-01-15'
        assert article.filename == 'test.txt'
        assert article.part == 1

    def test_formatted_date_property(self):
        """Test: formatted_date returns human-readable date."""
        article = Article(
            id='test',
            title='Test',
            date='2024-01-15',
            filename='test.txt',
            part=1
        )

        assert article.formatted_date == 'January 15, 2024'

    def test_date_obj_property(self):
        """Test: date_obj returns datetime object."""
        article = Article(
            id='test',
            title='Test',
            date='2024-01-15',
            filename='test.txt',
            part=1
        )

        date_obj = article.date_obj
        assert isinstance(date_obj, datetime)
        assert date_obj.year == 2024
        assert date_obj.month == 1
        assert date_obj.day == 15

    def test_optional_fields(self):
        """Test: Optional fields default to None."""
        article = Article(
            id='test',
            title='Test',
            date='2024-01-15',
            filename='test.txt',
            part=1
        )

        assert article.category_id is None
        assert article.content is None
        assert article.excerpt is None
        assert article.reading_time is None

    def test_with_optional_fields(self):
        """Test: Create article with all optional fields."""
        article = Article(
            id='test',
            title='Test',
            date='2024-01-15',
            filename='test.txt',
            part=1,
            category_id='category-1',
            content='Test content',
            excerpt='Test excerpt',
            reading_time=5
        )

        assert article.category_id == 'category-1'
        assert article.content == 'Test content'
        assert article.excerpt == 'Test excerpt'
        assert article.reading_time == 5


class TestBlogCategoryModel:
    """Test BlogCategory dataclass."""

    def test_category_creation(self, sample_category):
        """Test: Create category with articles."""
        assert sample_category.id == 'test-category'
        assert sample_category.name == 'Test Category'
        assert len(sample_category.articles) == 2

    def test_article_count_property(self, sample_category):
        """Test: article_count returns number of articles."""
        assert sample_category.article_count == 2

    def test_get_sorted_articles(self, sample_category):
        """Test: get_sorted_articles returns articles sorted by part."""
        sorted_articles = sample_category.get_sorted_articles()

        assert len(sorted_articles) == 2
        assert sorted_articles[0].part == 1
        assert sorted_articles[1].part == 2

    def test_get_article_by_id_found(self, sample_category):
        """Test: get_article_by_id returns correct article."""
        article = sample_category.get_article_by_id('article-1')

        assert article is not None
        assert article.id == 'article-1'
        assert article.part == 1

    def test_get_article_by_id_not_found(self, sample_category):
        """Test: get_article_by_id returns None for missing ID."""
        article = sample_category.get_article_by_id('nonexistent')
        assert article is None

    def test_empty_category(self):
        """Test: Category with no articles."""
        category = BlogCategory(
            id='empty',
            name='Empty Category',
            subtitle='Empty',
            description='Empty',
            image='empty.png',
            articles=[]
        )

        assert category.article_count == 0
        assert len(category.get_sorted_articles()) == 0


class TestVacancyModel:
    """Test Vacancy dataclass."""

    def test_vacancy_creation_with_enums(self):
        """Test: Create vacancy with enum values."""
        vacancy = Vacancy(
            name='Test Role',
            role_type=RoleType.MEDIUM,
            is_internal=True,
            stage=RecruitmentStage.INTERVIEW
        )

        assert vacancy.name == 'Test Role'
        assert vacancy.role_type == RoleType.MEDIUM
        assert vacancy.is_internal is True
        assert vacancy.stage == RecruitmentStage.INTERVIEW

    def test_vacancy_creation_with_strings(self):
        """Test: String values are converted to enums in __post_init__."""
        vacancy = Vacancy(
            name='Test Role',
            role_type='hard',
            is_internal=False,
            stage='screening'
        )

        assert vacancy.role_type == RoleType.HARD
        assert vacancy.stage == RecruitmentStage.SCREENING

    def test_role_type_case_insensitive(self):
        """Test: Role type string is case-insensitive."""
        for role_str in ['easy', 'EASY', 'Easy', 'EaSy']:
            vacancy = Vacancy(
                name='Test',
                role_type=role_str
            )
            assert vacancy.role_type == RoleType.EASY

    def test_stage_case_insensitive(self):
        """Test: Stage string is case-insensitive."""
        for stage_str in ['sourcing', 'SOURCING', 'Sourcing', 'SoUrCiNg']:
            vacancy = Vacancy(
                name='Test',
                role_type='easy',
                stage=stage_str
            )
            assert vacancy.stage == RecruitmentStage.SOURCING

    def test_empty_stage_converts_to_none(self):
        """Test: Empty string stage converts to NONE enum."""
        vacancy = Vacancy(
            name='Test',
            role_type='easy',
            stage=''
        )
        assert vacancy.stage == RecruitmentStage.NONE

    def test_default_values(self):
        """Test: Default values for optional fields."""
        vacancy = Vacancy(
            name='Test',
            role_type=RoleType.EASY
        )

        assert vacancy.is_internal is False
        assert vacancy.stage == RecruitmentStage.NONE

    def test_invalid_role_type_raises_error(self):
        """Test: Invalid role type raises ValueError."""
        with pytest.raises(ValueError):
            Vacancy(name='Test', role_type='invalid')

    def test_invalid_stage_raises_error(self):
        """Test: Invalid stage raises ValueError."""
        with pytest.raises(ValueError):
            Vacancy(name='Test', role_type='easy', stage='invalid_stage')


class TestRecruiterModel:
    """Test Recruiter dataclass."""

    def test_recruiter_creation(self, sample_recruiter):
        """Test: Create recruiter with vacancies."""
        assert sample_recruiter.name == 'Test Recruiter'
        assert len(sample_recruiter.vacancies) == 2

    def test_vacancy_count_property(self, sample_recruiter):
        """Test: vacancy_count returns number of vacancies."""
        assert sample_recruiter.vacancy_count == 2

    def test_empty_recruiter(self):
        """Test: Recruiter with no vacancies."""
        recruiter = Recruiter(name='Empty Recruiter', vacancies=[])

        assert recruiter.vacancy_count == 0
        assert recruiter.vacancies == []

    def test_default_vacancies(self):
        """Test: Vacancies default to empty list."""
        recruiter = Recruiter(name='Default')

        assert recruiter.vacancies == []
        assert recruiter.vacancy_count == 0


class TestRoleTypeEnum:
    """Test RoleType enumeration."""

    def test_enum_values(self):
        """Test: All role types have correct values."""
        assert RoleType.EASY.value == 'easy'
        assert RoleType.MEDIUM.value == 'medium'
        assert RoleType.HARD.value == 'hard'

    def test_enum_from_string(self):
        """Test: Create enum from string value."""
        assert RoleType('easy') == RoleType.EASY
        assert RoleType('medium') == RoleType.MEDIUM
        assert RoleType('hard') == RoleType.HARD


class TestRecruitmentStageEnum:
    """Test RecruitmentStage enumeration."""

    def test_enum_values(self):
        """Test: All stages have correct values."""
        assert RecruitmentStage.SOURCING.value == 'sourcing'
        assert RecruitmentStage.SCREENING.value == 'screening'
        assert RecruitmentStage.INTERVIEW.value == 'interview'
        assert RecruitmentStage.OFFER.value == 'offer'
        assert RecruitmentStage.PRE_HIRE_CHECKS.value == 'pre-hire checks'
        assert RecruitmentStage.NONE.value == ''

    def test_enum_from_string(self):
        """Test: Create enum from string value."""
        assert RecruitmentStage('sourcing') == RecruitmentStage.SOURCING
        assert RecruitmentStage('screening') == RecruitmentStage.SCREENING
        assert RecruitmentStage('') == RecruitmentStage.NONE
