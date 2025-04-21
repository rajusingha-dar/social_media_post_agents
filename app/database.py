# app/database.py
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from .config import settings

# Configure module logger
logger = logging.getLogger(__name__)

# Create MySQL engine
try:
    SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False
    )
    logger.info(f"Database engine created for {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
except Exception as e:
    logger.error(f"Failed to create database engine: {str(e)}")
    raise

# Create sessionmaker
try:
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info("Database session factory created")
except Exception as e:
    logger.error(f"Failed to create session factory: {str(e)}")
    raise

# Create base class for models
Base = declarative_base()

# Password context for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Helper functions
def get_db():
    """Dependency for database session management."""
    db = SessionLocal()
    try:
        logger.debug("Database session created")
        yield db
    finally:
        db.close()
        logger.debug("Database session closed")

def initialize_db():
    """Initialize database by creating all tables if they don't exist."""
    try:
        # Import models to ensure they're registered with SQLAlchemy
        from .models.user import User
        from .models.chat import Conversation, Message
        from .models.post import SocialMediaPost, PlatformType
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        return False