from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from decouple import config


load_dotenv()  # Load environment variables from .env file



class Settings(BaseSettings):
    
    # Environment Settings - either "dev", "staging", or "production"
    PYTHON_ENV: str 
    
    # Application settings
    APP_NAME: str 
    APP_DESCRIPTION: str 
    APP_VERSION: str 
    APP_SECRET_KEY: str
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    
    # Database configuration
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_TYPE: str
    
    # Security settings
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    ACCESS_SECRET_KEY: str
    REFRESH_SECRET_KEY: str
    
    # OAuth configuration
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str
    
    
    MAIL_FROM_NAME: str
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    
    # Redis configuration
    REDIS_URL: str
    
    @property
    def frontend_url(self) -> str:
        """
        Get the appropriate frontend URL based on environment and request origin
        """
        if self.PYTHON_ENV == "dev":
            # Local development always goes to localhost frontend
            return config("LOCAL_FRONTEND_URL", default="http://localhost:3000")
        
        elif self.PYTHON_ENV == "staging":
            # For staging, check if we should redirect to local or production
            return config("REDIRECT_URL", default="https://staging.vidkarma.ad")
        
        else:  # production
            return "https://vidkarma.ad"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        
        
Config = Settings()
