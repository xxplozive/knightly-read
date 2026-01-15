"""Handles article deduplication using both exact URL and fuzzy title matching."""
from typing import List, Tuple
from rapidfuzz import fuzz
from .parser import Article
import logging
import re

logger = logging.getLogger(__name__)


class ArticleDeduplicator:
    def __init__(self, similarity_threshold: float = 0.85):
        """
        Initialize deduplicator.

        Args:
            similarity_threshold: Minimum similarity ratio (0-1) for titles to be
                                  considered duplicates. Default 0.85 works well
                                  for news headlines.
        """
        self.similarity_threshold = similarity_threshold * 100  # rapidfuzz uses 0-100 scale

    def _normalize_title(self, title: str) -> str:
        """Normalize title for comparison by removing noise."""
        # Lowercase
        normalized = title.lower()
        # Remove common prefixes like "BREAKING:", "UPDATE:", etc.
        prefixes = ['breaking:', 'update:', 'live:', 'exclusive:', 'watch:', 'video:']
        for prefix in prefixes:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):].strip()
        # Remove punctuation for comparison
        normalized = re.sub(r'[^\w\s]', '', normalized)
        # Collapse whitespace
        normalized = ' '.join(normalized.split())
        return normalized

    def _are_titles_similar(self, title1: str, title2: str) -> Tuple[bool, float]:
        """Check if two titles are similar enough to be considered duplicates."""
        norm1 = self._normalize_title(title1)
        norm2 = self._normalize_title(title2)

        # Use token_sort_ratio which handles word order differences
        # e.g., "Biden meets Xi" vs "Xi meets Biden" will match
        score = fuzz.token_sort_ratio(norm1, norm2)

        return score >= self.similarity_threshold, score

    def deduplicate(self, articles: List[Article]) -> List[Article]:
        """
        Remove duplicate articles based on URL and fuzzy title matching.

        Strategy:
        1. First pass: Remove exact URL duplicates
        2. Second pass: Remove fuzzy title duplicates (keep the one from
           higher-priority source or earlier in list)
        """
        if not articles:
            return []

        # Phase 1: URL-based deduplication
        seen_urls = set()
        url_unique = []
        for article in articles:
            if article.url not in seen_urls:
                seen_urls.add(article.url)
                url_unique.append(article)

        logger.debug(f"URL dedup: {len(articles)} -> {len(url_unique)} articles")

        # Phase 2: Fuzzy title deduplication
        unique_articles = []

        for article in url_unique:
            is_duplicate = False

            for existing in unique_articles:
                similar, score = self._are_titles_similar(article.title, existing.title)
                if similar:
                    logger.debug(
                        f"Fuzzy duplicate ({score:.0f}%): "
                        f"'{article.title}' ({article.source}) ~ "
                        f"'{existing.title}' ({existing.source})"
                    )
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_articles.append(article)

        logger.info(f"Deduplication: {len(articles)} -> {len(unique_articles)} articles")
        return unique_articles
