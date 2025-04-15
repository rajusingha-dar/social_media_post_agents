# app/config.py
import os
import logging
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables with defaults.
    
    Attributes:
        SECRET_KEY: Secret key for JWT token generation
        ALGORITHM: Algorithm used for JWT
        ACCESS_TOKEN_EXPIRE_MINUTES: Token expiration time in minutes
        DB_HOST: Database host address
        DB_PORT: Database port
        DB_NAME: Database name
        DB_USER: Database username
        DB_PASSWORD: Database password
        OPENAI_API_KEY: Optional OpenAI API key
        TWITTER_API_KEY: Optional Twitter API key
        TWITTER_API_SECRET: Optional Twitter API secret
        FACEBOOK_ACCESS_TOKEN: Optional Facebook access token
        LINKEDIN_ACCESS_TOKEN: Optional LinkedIn access token
        REDDIT_CLIENT_ID: Optional Reddit client ID
        REDDIT_CLIENT_SECRET: Optional Reddit client secret
    """
    # Authentication settings
    SECRET_KEY: str = "YOUR_SECRET_KEY_HERE"  # Should be overridden in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database settings
    DB_HOST: str = "localhost"
    DB_PORT: str = "3306"
    DB_NAME: str = "ai_social_poster"
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    
    # OpenAI settings
    OPENAI_API_KEY: Optional[str] = None
    
    # Social media API keys
    TWITTER_API_KEY: Optional[str] = None
    TWITTER_API_SECRET: Optional[str] = None
    FACEBOOK_ACCESS_TOKEN: Optional[str] = None
    LINKEDIN_ACCESS_TOKEN: Optional[str] = None
    REDDIT_CLIENT_ID: Optional[str] = None
    REDDIT_CLIENT_SECRET: Optional[str] = None
    
    # Log level
    LOG_LEVEL: str = "INFO"
    
    @property
    def DATABASE_URL(self) -> str:
        """Constructs database connection URL from components."""
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

try:
    settings = Settings()
    logger.info("Settings loaded successfully")
    
    # Log warning if using default secret key in production
    if settings.SECRET_KEY == "YOUR_SECRET_KEY_HERE" and os.getenv("ENVIRONMENT", "").lower() == "production":
        logger.warning("Using default SECRET_KEY in production environment - this is insecure!")
    
    # Set log level based on settings
    logging.getLogger().setLevel(getattr(logging, settings.LOG_LEVEL))
    
except Exception as e:
    logger.error(f"Failed to load settings: {str(e)}")
    raise