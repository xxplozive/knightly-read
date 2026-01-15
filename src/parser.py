"""Parses RSS feeds and normalizes article data."""
import feedparser
from dateutil import parser as date_parser
from datetime import datetime, timezone
from typing import List, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Article:
    title: str
    url: str
    source: str
    published: datetime
    feed_position: int = 0
    popularity_score: float = 0.0
    is_paywalled: bool = False

    def calculate_popularity(self, total_items: int = 1) -> None:
        """
        Calculate popularity score based on feed position.

        Uses formula: score = 1 / (position + 1)
        This gives:
        - Position 0 (first item): score = 1.0
        - Position 1: score = 0.5
        - Position 2: score = 0.33
        """
        self.popularity_score = 1.0 / (self.feed_position + 1)

    def to_dict(self) -> dict:
        return {
            'title': self.title,
            'url': self.url,
            'source': self.source,
            'published': self.published.isoformat(),
            'age': self._format_age(),
            'popularity_score': round(self.popularity_score, 3),
            'feed_position': self.feed_position,
            'is_paywalled': self.is_paywalled
        }

    def _format_age(self) -> str:
        """Format time since publication (e.g., '2 hours ago')."""
        now = datetime.now(timezone.utc)
        pub = self.published
        if pub.tzinfo is None:
            pub = pub.replace(tzinfo=timezone.utc)
        delta = now - pub

        if delta.days > 0:
            return f"{delta.days}d ago"
        hours = delta.seconds // 3600
        if hours > 0:
            return f"{hours}h ago"
        minutes = delta.seconds // 60
        return f"{minutes}m ago"


class FeedParser:
    def parse(self, content: str, source_name: str) -> List[Article]:
        """Parse RSS content and return list of articles with position tracking."""
        if not content:
            return []

        try:
            feed = feedparser.parse(content)
            articles = []
            total_entries = len(feed.entries)

            for position, entry in enumerate(feed.entries):
                article = self._parse_entry(entry, source_name, position)
                if article:
                    article.calculate_popularity(total_entries)
                    articles.append(article)

            return articles
        except Exception as e:
            logger.error(f"Failed to parse feed from {source_name}: {e}")
            return []

    def _parse_entry(
        self,
        entry: Any,
        source_name: str,
        position: int = 0
    ) -> Optional[Article]:
        """Parse a single feed entry."""
        title = entry.get('title', '').strip()
        url = entry.get('link', '')

        if not title or not url:
            return None

        published = self._parse_date(entry)

        return Article(
            title=title,
            url=url,
            source=source_name,
            published=published,
            feed_position=position
        )

    def _parse_date(self, entry: Any) -> datetime:
        """Extract and parse publication date from entry."""
        date_fields = ['published', 'updated', 'created']

        for field in date_fields:
            if field in entry:
                try:
                    parsed = date_parser.parse(entry[field])
                    if parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=timezone.utc)
                    return parsed
                except (ValueError, TypeError):
                    pass

        return datetime.now(timezone.utc)
