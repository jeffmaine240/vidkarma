from enum import Enum


class TokenType(str, Enum):
    """Enum for token types."""
    ACCESS = "access"
    REFRESH = "refresh"
    

class AuthProvider(str, Enum):
    LOCAL = "local"
    GOOGLE = "google"
    FACEBOOK = "facebook"
    TWITTER = "twitter"
    GITHUB = "github"
    APPLE = "apple"
    
class Environment(str, Enum):
    LOCAL = "local"
    STAGING = "staging"
    PROD = "prod"