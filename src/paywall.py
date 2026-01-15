"""Detects paywalled content using curated list and meta tag heuristics."""
import requests
import re
from typing import Set, Optional
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class PaywallDetector:
    # Default known paywalled domains
    DEFAULT_PAYWALLED_DOMAINS = {
        'wsj.com',
        'nytimes.com',
        'ft.com',
        'economist.com',
        'washingtonpost.com',
        'bloomberg.com',
        'businessinsider.com',
        'theatlantic.com',
        'newyorker.com',
        'wired.com',
        'thetimes.co.uk',
        'telegraph.co.uk',
        'barrons.com',
    }

    # Paywall indicator patterns in HTML
    PAYWALL_META_PATTERNS = [
        r'isAccessibleForFree["\s:]+false',
        r'"isAccessibleForFree"\s*:\s*"False"',
        r'<meta[^>]+paywall',
        r'class=["\'][^"\']*paywall[^"\']*["\']',
        r'data-paywall',
        r'subscription-required',
        r'premium-content',
        r'subscriber-only',
    ]

    def __init__(
        self,
        paywalled_domains: Optional[Set[str]] = None,
        check_meta: bool = False,
        timeout: int = 5
    ):
        """
        Initialize PaywallDetector.

        Args:
            paywalled_domains: Set of known paywalled domains. If None, uses defaults.
            check_meta: Whether to fetch and check HTML meta tags for unknown sources.
            timeout: Timeout for meta tag checks.
        """
        self.paywalled_domains = paywalled_domains or self.DEFAULT_PAYWALLED_DOMAINS.copy()
        self.check_meta = check_meta
        self.timeout = timeout
        self._meta_cache = {}  # Cache meta check results

        # Compile regex patterns
        self._paywall_pattern = re.compile(
            '|'.join(self.PAYWALL_META_PATTERNS),
            re.IGNORECASE
        )

    def _extract_domain(self, url: str) -> str:
        """Extract the base domain from a URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove 'www.' prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except Exception:
            return ''

    def _is_known_paywalled(self, url: str) -> bool:
        """Check if URL is from a known paywalled domain."""
        domain = self._extract_domain(url)

        # Check exact match and subdomains
        for paywalled in self.paywalled_domains:
            if domain == paywalled or domain.endswith('.' + paywalled):
                return True
        return False

    def _check_meta_tags(self, url: str) -> bool:
        """Fetch page and check for paywall meta tags."""
        if url in self._meta_cache:
            return self._meta_cache[url]

        try:
            response = requests.get(
                url,
                timeout=self.timeout,
                headers={'User-Agent': 'Mozilla/5.0 (compatible; NewsAggregator/1.0)'}
            )

            # Only check first 50KB to save bandwidth
            content = response.text[:50000]

            has_paywall = bool(self._paywall_pattern.search(content))
            self._meta_cache[url] = has_paywall

            return has_paywall

        except Exception as e:
            logger.debug(f"Meta tag check failed for {url}: {e}")
            self._meta_cache[url] = False
            return False

    def is_paywalled(self, url: str) -> bool:
        """
        Check if an article URL is behind a paywall.

        Args:
            url: Article URL to check

        Returns:
            True if paywalled, False otherwise
        """
        # First check known domains (fast)
        if self._is_known_paywalled(url):
            logger.debug(f"Known paywalled source: {url}")
            return True

        # Optionally check meta tags (slower, but catches unknown sources)
        if self.check_meta:
            if self._check_meta_tags(url):
                logger.debug(f"Paywall detected via meta tags: {url}")
                return True

        return False

    def add_paywalled_domain(self, domain: str) -> None:
        """Add a domain to the paywalled list."""
        self.paywalled_domains.add(domain.lower())

    def remove_paywalled_domain(self, domain: str) -> None:
        """Remove a domain from the paywalled list."""
        self.paywalled_domains.discard(domain.lower())
