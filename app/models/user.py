# app/models/user.py
from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship
import logging
from ..database import Base

logger = logging.getLogger(__name__)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(100))
    is_active = Column(Boolean, default=True)
    
    # Add these classmethods that were previously in database.py
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