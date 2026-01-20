"""
Blog Service - Handles all blog-related business logic

This service encapsulates article content retrieval, parsing, enrichment,
and metadata calculations.
"""

import re
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime
from models import Article, BlogCategory


class BlogService:
    """Service for managing blog articles and content."""

    def __init__(self, articles_dir: Path):
        """
        Initialize the blog service.

        Args:
            articles_dir: Path to the directory containing article files
        """
        self.articles_dir = articles_dir

    def get_article_content(self, filename: str) -> Optional[str]:
        """
        Safely read article content with path validation.

        Args:
            filename: Name of the article file

        Returns:
            Article content as string, or None if not found/invalid
        """
        # Validate filename - only allow alphanumeric, dash, underscore, and dot
        if not filename or not re.match(r'^[\w\-\.]+$', filename):
            return None

        filepath = (self.articles_dir / filename).resolve()

        # Ensure the resolved path is still within articles directory (prevents traversal)
        try:
            filepath.relative_to(self.articles_dir)
        except ValueError:
            # Path is outside articles directory
            return None

        # Read file with error handling
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except (FileNotFoundError, PermissionError):
            return None

    def calculate_reading_time(self, text: str) -> int:
        """
        Calculate estimated reading time based on word count.

        Args:
            text: Article content

        Returns:
            Estimated reading time in minutes (minimum 1)
        """
        words = len(text.split())
        return max(1, round(words / 200))

    def get_excerpt(self, text: str, sentence_count: int = 2) -> str:
        """
        Extract an excerpt from article text.

        Args:
            text: Full article content
            sentence_count: Number of sentences to include

        Returns:
            Excerpt string (max 200 characters)
        """
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        excerpt = ' '.join(sentences[:sentence_count])
        return (excerpt[:197] + '...') if len(excerpt) > 200 else excerpt

    def parse_content(self, text: str) -> List[dict]:
        """
        Parse article content into structured blocks.

        Args:
            text: Raw article text

        Returns:
            List of content blocks with type and content
        """
        blocks = []
        for para in [p.strip() for p in text.split("\n\n") if p.strip()]:
            is_heading = (
                re.match(r'^Part\s+\d+', para, re.IGNORECASE) or
                (len(para) < 80 and not para.endswith('.'))
            )
            blocks.append({
                "type": "heading" if is_heading else "paragraph",
                "content": para
            })
        return blocks

    def enrich_article(self, article: Article) -> Article:
        """
        Populate article with dynamic content and metadata.

        Creates a new Article instance with content, reading time, and excerpt populated.

        Args:
            article: Base article object

        Returns:
            New Article instance with enriched data
        """
        content = self.get_article_content(article.filename)

        if content:
            # Create enriched copy with all data
            return Article(
                id=article.id,
                title=article.title,
                date=article.date,
                filename=article.filename,
                part=article.part,
                category_id=article.category_id,
                content=content,
                reading_time=self.calculate_reading_time(content),
                excerpt=self.get_excerpt(content)
            )
        else:
            # Return original if content can't be loaded
            return Article(
                id=article.id,
                title=article.title,
                date=article.date,
                filename=article.filename,
                part=article.part,
                category_id=article.category_id,
                content=None,
                reading_time=0,
                excerpt=""
            )

    def get_category_articles(self, category: BlogCategory) -> List[Article]:
        """
        Get all articles for a category with enriched data.

        Args:
            category: BlogCategory object

        Returns:
            List of enriched Article objects sorted by part number
        """
        enriched_articles = [self.enrich_article(article) for article in category.articles]
        return sorted(enriched_articles, key=lambda x: x.part)

    def get_latest_article(self, categories: dict) -> Optional[Article]:
        """
        Get the most recent article across all categories.

        Args:
            categories: Dictionary of category_id -> BlogCategory

        Returns:
            Latest Article with enriched data and category_name attribute, or None
        """
        latest, latest_date, latest_category = None, None, None

        for cat_id, category in categories.items():
            for article in category.articles:
                if latest_date is None or article.date_obj > latest_date:
                    latest, latest_date, latest_category = article, article.date_obj, category

        if latest and latest_category:
            enriched = self.enrich_article(latest)
            # Add category name as attribute for template convenience
            enriched.category_name = latest_category.name
            return enriched

        return None

    def get_prev_next_articles(self, category: BlogCategory, current_part: int) -> Tuple[Optional[Article], Optional[Article]]:
        """
        Get previous and next articles for navigation.

        Args:
            category: BlogCategory object
            current_part: Current article part number

        Returns:
            Tuple of (previous_article, next_article), either can be None
        """
        prev_article, next_article = None, None

        for article in category.articles:
            if article.part == current_part - 1:
                prev_article = article
            elif article.part == current_part + 1:
                next_article = article

        return prev_article, next_article
