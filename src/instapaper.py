"""Instapaper integration for saving articles."""
import os
import json
import requests
from requests_oauthlib import OAuth1
from pathlib import Path
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class InstapaperClient:
    """
    Instapaper API client using xAuth (simplified OAuth).

    Instapaper uses xAuth which allows direct username/password authentication
    without the full OAuth dance. This is simpler for CLI/personal use.

    API docs: https://www.instapaper.com/api
    """

    BASE_URL = "https://www.instapaper.com/api/1"

    def __init__(
        self,
        consumer_key: Optional[str] = None,
        consumer_secret: Optional[str] = None,
        token_file: Optional[str] = None
    ):
        """
        Initialize Instapaper client.

        Args:
            consumer_key: Instapaper API consumer key (or INSTAPAPER_CONSUMER_KEY env var)
            consumer_secret: Instapaper API consumer secret (or INSTAPAPER_CONSUMER_SECRET env var)
            token_file: Path to store OAuth tokens (default: ~/.instapaper_tokens.json)
        """
        self.consumer_key = consumer_key or os.environ.get('INSTAPAPER_CONSUMER_KEY')
        self.consumer_secret = consumer_secret or os.environ.get('INSTAPAPER_CONSUMER_SECRET')
        self.token_file = Path(token_file or os.path.expanduser('~/.instapaper_tokens.json'))

        self.oauth_token = None
        self.oauth_token_secret = None

        # Load existing tokens if available
        self._load_tokens()

    def _load_tokens(self) -> bool:
        """Load OAuth tokens from file."""
        if self.token_file.exists():
            try:
                with open(self.token_file, 'r') as f:
                    data = json.load(f)
                    self.oauth_token = data.get('oauth_token')
                    self.oauth_token_secret = data.get('oauth_token_secret')
                    return True
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load tokens: {e}")
        return False

    def _save_tokens(self) -> None:
        """Save OAuth tokens to file."""
        try:
            with open(self.token_file, 'w') as f:
                json.dump({
                    'oauth_token': self.oauth_token,
                    'oauth_token_secret': self.oauth_token_secret
                }, f)
            # Secure the file
            self.token_file.chmod(0o600)
        except IOError as e:
            logger.error(f"Failed to save tokens: {e}")

    def _get_oauth(self) -> OAuth1:
        """Get OAuth1 authentication object."""
        return OAuth1(
            self.consumer_key,
            client_secret=self.consumer_secret,
            resource_owner_key=self.oauth_token,
            resource_owner_secret=self.oauth_token_secret
        )

    def is_authenticated(self) -> bool:
        """Check if we have valid authentication tokens."""
        return bool(self.oauth_token and self.oauth_token_secret)

    def authenticate(self, username: str, password: str) -> Tuple[bool, str]:
        """
        Authenticate with Instapaper using xAuth.

        Args:
            username: Instapaper username or email
            password: Instapaper password

        Returns:
            Tuple of (success, message)
        """
        if not self.consumer_key or not self.consumer_secret:
            return False, "Missing Instapaper API credentials. Set INSTAPAPER_CONSUMER_KEY and INSTAPAPER_CONSUMER_SECRET environment variables."

        oauth = OAuth1(self.consumer_key, client_secret=self.consumer_secret)

        try:
            response = requests.post(
                f"{self.BASE_URL}/oauth/access_token",
                auth=oauth,
                data={
                    'x_auth_username': username,
                    'x_auth_password': password,
                    'x_auth_mode': 'client_auth'
                }
            )

            if response.status_code == 200:
                # Parse response (format: oauth_token=xxx&oauth_token_secret=yyy)
                params = dict(p.split('=') for p in response.text.split('&'))
                self.oauth_token = params.get('oauth_token')
                self.oauth_token_secret = params.get('oauth_token_secret')
                self._save_tokens()
                return True, "Authentication successful"
            else:
                return False, f"Authentication failed: {response.text}"

        except requests.RequestException as e:
            return False, f"Request failed: {e}"

    def add_bookmark(
        self,
        url: str,
        title: Optional[str] = None,
        description: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Add a bookmark to Instapaper.

        Args:
            url: URL to bookmark
            title: Optional title override
            description: Optional description

        Returns:
            Tuple of (success, message)
        """
        if not self.is_authenticated():
            return False, "Not authenticated. Please authenticate first."

        data = {'url': url}
        if title:
            data['title'] = title
        if description:
            data['description'] = description

        try:
            response = requests.post(
                f"{self.BASE_URL}/bookmarks/add",
                auth=self._get_oauth(),
                data=data
            )

            if response.status_code == 200:
                result = response.json()
                bookmark_id = result[0].get('bookmark_id', 'unknown')
                return True, f"Article saved (ID: {bookmark_id})"
            else:
                return False, f"Failed to save: {response.text}"

        except requests.RequestException as e:
            return False, f"Request failed: {e}"

    def verify_credentials(self) -> Tuple[bool, str]:
        """Verify that stored credentials are still valid."""
        if not self.is_authenticated():
            return False, "No credentials stored"

        try:
            response = requests.post(
                f"{self.BASE_URL}/account/verify_credentials",
                auth=self._get_oauth()
            )

            if response.status_code == 200:
                user = response.json()[0]
                username = user.get('username', 'unknown')
                return True, f"Authenticated as {username}"
            else:
                return False, "Credentials invalid or expired"

        except requests.RequestException as e:
            return False, f"Verification failed: {e}"

    def logout(self) -> None:
        """Clear stored credentials."""
        self.oauth_token = None
        self.oauth_token_secret = None
        if self.token_file.exists():
            self.token_file.unlink()
