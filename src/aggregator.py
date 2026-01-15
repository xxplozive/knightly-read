"""Main aggregation logic - combines feeds by region."""
import yaml
from pathlib import Path
from typing import Dict, List
from .fetcher import FeedFetcher, RetryConfig
from .parser import FeedParser, Article
from .deduplicator import ArticleDeduplicator
from .paywall import PaywallDetector
import logging
import time

logger = logging.getLogger(__name__)


class NewsAggregator:
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)

        # Build retry config from settings
        retry_settings = self.config['settings'].get('retry', {})
        retry_config = RetryConfig(
            max_attempts=retry_settings.get('max_attempts', 3),
            base_delay=retry_settings.get('base_delay', 1.0),
            multiplier=retry_settings.get('multiplier', 2.0)
        )

        self.fetcher = FeedFetcher(
            user_agent=self.config['settings']['user_agent'],
            timeout=self.config['settings']['request_timeout'],
            retry_config=retry_config
        )
        self.parser = FeedParser()
        self.rate_limit_delay = self.config['settings'].get('rate_limit_delay', 0.5)

        # Initialize deduplicator
        dedup_settings = self.config['settings'].get('deduplication', {})
        self.deduplicator = ArticleDeduplicator(
            similarity_threshold=dedup_settings.get('similarity_threshold', 0.85)
        )

        # Initialize paywall detector
        paywall_settings = self.config['settings'].get('paywall', {})
        if paywall_settings.get('enabled', True):
            domains = set(paywall_settings.get('known_paywalled_domains', []))
            self.paywall_detector = PaywallDetector(
                paywalled_domains=domains if domains else None,
                check_meta=paywall_settings.get('check_meta_tags', False)
            )
        else:
            self.paywall_detector = None

    def _load_config(self, path: str) -> dict:
        with open(path, 'r') as f:
            return yaml.safe_load(f)

    def aggregate(self) -> Dict[str, dict]:
        """Aggregate headlines for all regions."""
        results = {}
        limit = self.config['settings']['headlines_per_region']
        sort_by = self.config['settings'].get('sort_by', 'published')

        for region_id, region_data in self.config['regions'].items():
            logger.info(f"Processing region: {region_data['name']}")
            articles = self._process_region(region_data)

            # Sort based on config
            if sort_by == 'popularity':
                articles.sort(key=lambda a: a.popularity_score, reverse=True)
            else:
                articles.sort(key=lambda a: a.published, reverse=True)

            results[region_id] = {
                'name': region_data['name'],
                'articles': [a.to_dict() for a in articles[:limit]]
            }

        return results

    def _process_region(self, region_data: dict) -> List[Article]:
        """Process all feeds for a region."""
        all_articles = []

        for feed_config in region_data['feeds']:
            url = feed_config['url']
            name = feed_config['name']
            timeout = feed_config.get('timeout')  # Per-feed timeout override

            logger.debug(f"Fetching {name}: {url}")
            content = self.fetcher.fetch(url, timeout=timeout)

            if content:
                articles = self.parser.parse(content, name)

                # Check for paywalls
                if self.paywall_detector:
                    for article in articles:
                        article.is_paywalled = self.paywall_detector.is_paywalled(article.url)

                all_articles.extend(articles)
                logger.info(f"Got {len(articles)} articles from {name}")
            else:
                logger.warning(f"No content from {name}")

            time.sleep(self.rate_limit_delay)

        # Deduplicate by URL and fuzzy title matching
        return self.deduplicator.deduplicate(all_articles)
