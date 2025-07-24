from datetime import timedelta
import secrets
from passlib.context import CryptContext
from jose import ExpiredSignatureError, JWTError, jwt
import redis 

from app.api.dependencies.custom_exception import InvalidTokenError
from app.schemas.enums import TokenType
from app.schemas.token import Token, TokenCreate, TokenData, TokenDetails

from .config import Config
from app.db.base_model import utcnow






class Security:
    """Security class for handling password hashing and JWT token creation."""
    
    def __init__(self):
        """Initialize the security class with secret keys and password context."""
        self.access_secret_key = Config.APP_SECRET_KEY
        self.refresh_secret_key = Config.REFRESH_SECRET_KEY
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.redis_client = redis.Redis.from_url(Config.REDIS_URL, decode_responses=True)
        
        
    def hash_password(self, password: str) -> str:
        """Hashes a password using bcrypt."""
        return self.pwd_context.hash(password)
    
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifies a plain password against a hashed password.
        Returns True if they match, False otherwise.
        """
        
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def create_token(self, token_data: TokenCreate) -> str:
        """Creates a JWT token."""

        if token_data.token_type == TokenType.ACCESS:
            secret_key = self.access_secret_key
            expire = utcnow() + timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
        else:
            secret_key = self.refresh_secret_key
            expire = utcnow() + timedelta(minutes=Config.REFRESH_TOKEN_EXPIRE_MINUTES)
        
        to_encode = {
            "sub": token_data.user_id,
            "type": token_data.token_type.value,
            "iat": int(utcnow().timestamp()),
            "exp": int(expire.timestamp())
        }

        return jwt.encode(to_encode, secret_key, algorithm=Config.ALGORITHM)
    
    
    def decode_token(self, data: TokenDetails) -> dict:
        """Decodes a JWT token and validates it."""
        secret_key = self.access_secret_key if data.token_type == TokenType.ACCESS else self.refresh_secret_key
        try:
            payload = jwt.decode(data.token, secret_key, algorithms=[Config.ALGORITHM])
            return payload
        except ExpiredSignatureError:
            raise InvalidTokenError("Token has expired.")
        except JWTError:
            raise InvalidTokenError("Invalid token.")
        
    
    
    def is_refresh_token_active(self, token: Token) -> bool:
        """Check if refresh token is valid (not blacklisted).

        Args:
            refresh_token: Token to check

        Returns:
            bool: True if token is active
        """
        blacklisted = self.redis_client.get(f"blacklisted_token:{token.token}")
        return blacklisted is None
    
    def refresh_access_token(self, current_refresh_token: Token)->tuple[str, str]:
        """Generate new access and refresh tokens.

        Args:
            current_refresh_token: Valid refresh token

        Returns:
            tuple: (new_access_token, new_refresh_token)

        Raises:
            HTTPException: If refresh token is invalid
        """

        token = self.verify_refresh_token(refresh_token=current_refresh_token)

        if token:
            access = self.create_token(token_data=TokenCreate(user_id=token.user_id, token_type=TokenType.access))
            refresh = self.create_token(token_data=TokenCreate(user_id=token.user_id, token_type=TokenType.REFRESH))

            return access, refresh
    
    
    def verify_refresh_token(self, refresh_token: Token)-> TokenData:
        
        payload = self.decode_token(
            data=TokenDetails(
                token=refresh_token.token,
                token_type=TokenType.REFRESH
            )
        )
        user_id = payload.get("sub")

        if user_id is None:
            raise InvalidTokenError()
        
        return TokenData(user_id=user_id)
    
    def generate_random_hex(self):
        """Generate random hex"""
        return secrets.token_urlsafe(16)


security = Security()

