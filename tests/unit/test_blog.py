"""
Unit Tests for BlogService

Tests the actual blog service logic from services/blog_service.py.
"""

import pytest
from pathlib import Path


class TestReadingTimeCalculation:
    """Test reading time estimation."""

    def test_short_text(self, blog_service):
        """Test: Short text gets minimum 1 minute."""
        text = "This is a very short text."
        time = blog_service.calculate_reading_time(text)
        assert time == 1  # Minimum

    def test_200_words(self, blog_service):
        """Test: 200 words = 1 minute (baseline)."""
        text = " ".join(["word"] * 200)
        time = blog_service.calculate_reading_time(text)
        assert time == 1

    def test_400_words(self, blog_service):
        """Test: 400 words = 2 minutes."""
        text = " ".join(["word"] * 400)
        time = blog_service.calculate_reading_time(text)
        assert time == 2

    def test_rounding(self, blog_service):
        """Test: Proper rounding (250 words rounds to 1)."""
        text = " ".join(["word"] * 250)
        time = blog_service.calculate_reading_time(text)
        assert time == 1  # 250/200 = 1.25, rounds to 1


class TestExcerptGeneration:
    """Test article excerpt creation."""

    def test_default_two_sentences(self, blog_service):
        """Test: Extract first 2 sentences by default."""
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        excerpt = blog_service.get_excerpt(text)
        assert excerpt == "First sentence. Second sentence."

    def test_custom_sentence_count(self, blog_service):
        """Test: Custom sentence count."""
        text = "One. Two. Three. Four."
        excerpt = blog_service.get_excerpt(text, sentence_count=3)
        assert excerpt == "One. Two. Three."

    def test_long_excerpt_truncation(self, blog_service):
        """Test: Excerpts >200 chars get truncated with ellipsis."""
        long_sentence = "This is a very long sentence " * 20  # > 200 chars
        text = f"{long_sentence}. Second sentence."
        excerpt = blog_service.get_excerpt(text)

        assert len(excerpt) == 200
        assert excerpt.endswith('...')

    def test_strip_whitespace(self, blog_service):
        """Test: Whitespace is properly stripped."""
        text = "  \n  First sentence.   Second sentence.  \n  "
        excerpt = blog_service.get_excerpt(text)
        assert excerpt == "First sentence. Second sentence."


class TestContentParsing:
    """Test article content parsing into blocks."""

    def test_paragraph_detection(self, blog_service):
        """Test: Regular paragraphs are parsed correctly."""
        text = "First paragraph.\n\nSecond paragraph."
        blocks = blog_service.parse_content(text)

        assert len(blocks) == 2
        assert blocks[0]['type'] == 'paragraph'
        assert blocks[0]['content'] == 'First paragraph.'
        assert blocks[1]['type'] == 'paragraph'
        assert blocks[1]['content'] == 'Second paragraph.'

    def test_heading_detection_part_number(self, blog_service):
        """Test: 'Part X' strings are detected as headings."""
        text = "Part 1: Introduction\n\nSome content."
        blocks = blog_service.parse_content(text)

        assert blocks[0]['type'] == 'heading'
        assert 'Part 1' in blocks[0]['content']

    def test_heading_detection_short_line(self, blog_service):
        """Test: Short lines without periods are headings."""
        text = "Short Heading\n\nThis is a longer paragraph with proper punctuation."
        blocks = blog_service.parse_content(text)

        assert blocks[0]['type'] == 'heading'
        assert blocks[0]['content'] == 'Short Heading'

    def test_empty_paragraphs_ignored(self, blog_service):
        """Test: Empty paragraphs are filtered out."""
        text = "Paragraph 1.\n\n\n\n\n\nParagraph 2."
        blocks = blog_service.parse_content(text)

        assert len(blocks) == 2
        assert all(block['content'] for block in blocks)


class TestArticleEnrichment:
    """Test article enrichment with dynamic data."""

    def test_enrich_with_nonexistent_file(self, blog_service, sample_article):
        """Test: Enrichment with missing file returns article with None content."""
        enriched = blog_service.enrich_article(sample_article)

        assert enriched.id == sample_article.id
        assert enriched.title == sample_article.title
        assert enriched.content is None
        assert enriched.reading_time == 0
        assert enriched.excerpt == ""

    def test_enrich_preserves_original_data(self, blog_service, sample_article):
        """Test: Original article data is preserved."""
        enriched = blog_service.enrich_article(sample_article)

        assert enriched.id == sample_article.id
        assert enriched.title == sample_article.title
        assert enriched.date == sample_article.date
        assert enriched.filename == sample_article.filename
        assert enriched.part == sample_article.part
        assert enriched.category_id == sample_article.category_id


class TestCategoryArticles:
    """Test getting articles for a category."""

    def test_get_category_articles_sorted(self, blog_service, sample_category):
        """Test: Articles are returned sorted by part number."""
        articles = blog_service.get_category_articles(sample_category)

        assert len(articles) == 2
        assert articles[0].part == 1
        assert articles[1].part == 2

    def test_enrichment_applied(self, blog_service, sample_category):
        """Test: Articles are enriched with content data."""
        articles = blog_service.get_category_articles(sample_category)

        for article in articles:
            # Should have content-related fields (even if None)
            assert hasattr(article, 'content')
            assert hasattr(article, 'reading_time')
            assert hasattr(article, 'excerpt')


class TestLatestArticle:
    """Test finding latest article across categories."""

    def test_latest_article_by_date(self, blog_service):
        """Test: Returns article with most recent date."""
        from models import Article, BlogCategory

        categories = {
            'cat1': BlogCategory(
                id='cat1',
                name='Category 1',
                subtitle='Sub 1',
                description='Desc 1',
                image='img1.png',
                articles=[
                    Article(id='old', title='Old', date='2024-01-01', filename='old.txt', part=1),
                ]
            ),
            'cat2': BlogCategory(
                id='cat2',
                name='Category 2',
                subtitle='Sub 2',
                description='Desc 2',
                image='img2.png',
                articles=[
                    Article(id='new', title='New', date='2024-12-31', filename='new.txt', part=1),
                ]
            ),
        }

        latest = blog_service.get_latest_article(categories)

        assert latest is not None
        assert latest.id == 'new'
        assert latest.date == '2024-12-31'

    def test_latest_article_has_category_name(self, blog_service):
        """Test: Latest article has category_name attribute."""
        from models import Article, BlogCategory

        categories = {
            'test': BlogCategory(
                id='test',
                name='Test Category',
                subtitle='Test',
                description='Test',
                image='test.png',
                articles=[
                    Article(id='article', title='Title', date='2024-01-01', filename='test.txt', part=1),
                ]
            ),
        }

        latest = blog_service.get_latest_article(categories)

        assert hasattr(latest, 'category_name')
        assert latest.category_name == 'Test Category'

    def test_empty_categories(self, blog_service):
        """Test: Empty categories returns None."""
        latest = blog_service.get_latest_article({})
        assert latest is None


class TestPrevNextArticles:
    """Test article navigation."""

    def test_prev_next_navigation(self, blog_service, sample_category):
        """Test: Get previous and next articles."""
        prev, next = blog_service.get_prev_next_articles(sample_category, current_part=1)

        assert prev is None  # Part 1 has no previous
        assert next is not None
        assert next.part == 2

    def test_middle_article(self, blog_service):
        """Test: Middle article has both prev and next."""
        from models import Article, BlogCategory

        category = BlogCategory(
            id='test',
            name='Test',
            subtitle='Test',
            description='Test',
            image='test.png',
            articles=[
                Article(id='a1', title='1', date='2024-01-01', filename='1.txt', part=1),
                Article(id='a2', title='2', date='2024-01-02', filename='2.txt', part=2),
                Article(id='a3', title='3', date='2024-01-03', filename='3.txt', part=3),
            ]
        )

        prev, next = blog_service.get_prev_next_articles(category, current_part=2)

        assert prev.part == 1
        assert next.part == 3

    def test_last_article(self, blog_service, sample_category):
        """Test: Last article has no next."""
        prev, next = blog_service.get_prev_next_articles(sample_category, current_part=2)

        assert prev.part == 1
        assert next is None  # Part 2 is last
