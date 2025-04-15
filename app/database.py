# app/database.py
import logging
from sqlalchemy import create_engine, Column, Integer, String, Boolean
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
        pool_pre_ping=True,  # Check connection validity before using it
        pool_recycle=3600,   # Recycle connections older than 1 hour
        echo=False           # Set to True to log all SQL queries (verbose)
    )
    logger.info(f"Database engine created for {SQLALCHEMY_DATABASE_URL.split('@')[1]}")
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

# User model - Removed created_at and updated_at fields
class User(Base):
    """
    User model for authentication and profile information.
    
    Attributes:
        id: Primary key
        username: Unique username
        email: Unique email address
        hashed_password: Encrypted password
        is_active: Whether the user account is active
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    @classmethod
    def get_by_email(cls, db, email):
        """Get a user by email address."""
        try:
            user = db.query(cls).filter(cls.email == email).first()
            return user
        except Exception as e:
            logger.error(f"Database error when getting user by email: {str(e)}")
            return None
    
    @classmethod
    def get_by_username(cls, db, username):
        """Get a user by username."""
        try:
            user = db.query(cls).filter(cls.username == username).first()
            return user
        except Exception as e:
            logger.error(f"Database error when getting user by username: {str(e)}")
            return None

    def __repr__(self):
        """String representation of User object."""
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

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
        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        return False