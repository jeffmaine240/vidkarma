from authlib.integrations.starlette_client import OAuth
from app.core.config import Config


class OAuthSettings:
    """Centralized OAuth Configuration Management"""

    GOOGLE_CONF_URL = "https://accounts.google.com/.well-known/openid-configuration"

    @classmethod
    def get_google_oauth_client(cls):
        oauth = OAuth()
        oauth.register(
            name="google",
            client_id=Config.GOOGLE_CLIENT_ID,
            client_secret=Config.GOOGLE_CLIENT_SECRET,
            server_metadata_url=cls.GOOGLE_CONF_URL,
            client_kwargs={
                "scope": "openid email profile"
            },
        )
        return oauth

