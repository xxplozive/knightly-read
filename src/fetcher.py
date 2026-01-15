"""Fetches RSS feeds with proper error handling, rate limiting, and retry logic."""
import requests
import logging
import time
from typing import Optional, Dict, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """Configuration for retry behavior with exponential backoff."""
    max_attempts: int = 3
    base_delay: float = 1.0
    multiplier: float = 2.0


class FeedFetcher:
    def __init__(
        self,
        user_agent: str,
        timeout: int = 15,
        retry_config: Optional[RetryConfig] = None
    ):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'application/rss+xml, application/xml, text/xml, */*'
        })
        self.timeout = timeout
        self.retry_config = retry_config or RetryConfig()

    def fetch(self, url: str, timeout: Optional[int] = None) -> Optional[str]:
        """Fetch RSS feed content from URL with retry logic.

        Args:
            url: The feed URL to fetch
            timeout: Optional per-request timeout override
        """
        effective_timeout = timeout if timeout is not None else self.timeout

        for attempt in range(self.retry_config.max_attempts):
            try:
                response = self.session.get(url, timeout=effective_timeout)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                is_last_attempt = attempt == self.retry_config.max_attempts - 1

                if is_last_attempt:
                    logger.warning(f"Failed to fetch {url} after {self.retry_config.max_attempts} attempts: {e}")
                    return None

                # Calculate exponential backoff delay
                delay = self.retry_config.base_delay * (self.retry_config.multiplier ** attempt)
                logger.info(f"Retry {attempt + 1}/{self.retry_config.max_attempts} for {url} in {delay:.1f}s: {e}")
                time.sleep(delay)

        return None

    def fetch_all(self, urls: List[str], delay: float = 0.5) -> Dict[str, Optional[str]]:
        """Fetch multiple feeds with rate limiting."""
        results = {}
        for url in urls:
            results[url] = self.fetch(url)
            time.sleep(delay)
        return results
