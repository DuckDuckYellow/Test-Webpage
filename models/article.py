"""
Blog article and category models.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Article:
    """Represents a blog article."""
    id: str
    title: str
    date: str  # Format: YYYY-MM-DD
    filename: str
    part: int
    category_id: Optional[str] = None

    # These will be populated by the Service layer in Phase 4,
    # but the model should accommodate them.
    content: Optional[str] = None
    excerpt: Optional[str] = None
    reading_time: Optional[int] = None

    @property
    def formatted_date(self) -> str:
        """Return human-readable date."""
        date_obj = datetime.strptime(self.date, "%Y-%m-%d")
        return date_obj.strftime("%B %d, %Y")

    @property
    def date_obj(self) -> datetime:
        """Return datetime object for sorting."""
        return datetime.strptime(self.date, "%Y-%m-%d")


@dataclass
class BlogCategory:
    """Represents a blog category containing articles."""
    id: str
    name: str
    subtitle: str
    description: str
    image: str
    articles: List[Article] = field(default_factory=list)

    @property
    def article_count(self) -> int:
        """Return count of articles in this category."""
        return len(self.articles)

    def get_sorted_articles(self) -> List[Article]:
        """Return articles sorted by part number."""
        return sorted(self.articles, key=lambda x: x.part)

    def get_article_by_id(self, article_id: str) -> Optional[Article]:
        """Find article by ID."""
        return next((a for a in self.articles if a.id == article_id), None)
