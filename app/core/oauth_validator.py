import re
import sys
import logging
import requests
from typing import Dict

from core.config import Config
from api.dependencies.custom_exception import GoogleOAuthConfigError
from utils.logger import get_logger


logger = get_logger(__name__)


def validate_google_client_id(client_id: str) -> bool:
    """Validate the Google OAuth client ID format."""
    pattern = r"^[\d-]+\.apps\.googleusercontent\.com$"
    return bool(re.match(pattern, client_id))


def validate_redirect_uri(uri: str) -> bool:
    """Validate that the redirect URI is an HTTP(S) URI."""
    return uri.startswith("http://") or uri.startswith("https://")


def check_discovery_endpoint(timeout: int = 5) -> bool:
    """Check if Google's OpenID configuration endpoint is reachable."""
    discovery_url = "https://accounts.google.com/.well-known/openid-configuration"
    try:
        response = requests.get(discovery_url, timeout=timeout)
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        logger.error("Could not connect to Google Discovery Endpoint", exc_info=e)
        return False


def validate_google_oauth_config() -> None:
    """
    Validates Google OAuth config. Raises an exception if any part fails.
    """
    logger.info("🔍 Validating Google OAuth Configuration...")

    config: Dict[str, str] = {
        "GOOGLE_CLIENT_ID": Config.GOOGLE_CLIENT_ID,
        "GOOGLE_CLIENT_SECRET": Config.GOOGLE_CLIENT_SECRET,
        "GOOGLE_REDIRECT_URI": Config.GOOGLE_REDIRECT_URI,
    }

    for key, value in config.items():
        if not value:
            raise GoogleOAuthConfigError(f"{key} is not set in environment/config.")
        logger.debug(f"{key}: {value}")

    if not validate_google_client_id(config["GOOGLE_CLIENT_ID"]):
        raise GoogleOAuthConfigError("Invalid GOOGLE_CLIENT_ID format.")

    if not validate_redirect_uri(config["GOOGLE_REDIRECT_URI"]):
        raise GoogleOAuthConfigError("Invalid GOOGLE_REDIRECT_URI format.")

    if not check_discovery_endpoint():
        raise GoogleOAuthConfigError("Failed to reach Google's OAuth Discovery Endpoint.")

    logger.info("✅ Google OAuth configuration passed all checks.")
    logger.info("📋 Google Cloud Console Checklist:")
    logger.info("- Redirect URIs are registered:")
    logger.info("  • http://127.0.0.1:8000/api/v1/oauth/google/callback")
    logger.info("  • http://localhost:8000/api/v1/oauth/google/callback")
    logger.info("- OAuth consent screen is configured")
    logger.info("- App is in 'Testing' or 'Production' status")


def main() -> None:
    try:
        validate_google_oauth_config()
        logger.info("Google OAuth validation completed successfully.")
        sys.exit(0)
    except GoogleOAuthConfigError as e:
        logger.error(f"OAuth Config Validation Failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical("Unexpected error during OAuth validation", exc_info=e)
        sys.exit(1)


if __name__ == "__main__":
    main()
