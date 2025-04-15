# app/auth.py
import logging
from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, validator

from .database import User, get_db, pwd_context
from .config import settings

# Configure module logger
logger = logging.getLogger(__name__)

# JWT settings
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")

# Models
class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str
    
class TokenData(BaseModel):
    """Token data model for decoded JWT payloads."""
    username: Optional[str] = None
    
class UserCreate(BaseModel):
    """User creation request model."""
    username: str
    email: EmailStr
    password: str
    
    @validator('username')
    def username_must_be_valid(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if len(v) > 50:
            raise ValueError('Username must be less than 50 characters')
        return v
    
    @validator('password')
    def password_must_be_strong(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v
    
class UserResponse(BaseModel):
    """User response model with sensitive data removed."""
    id: int
    username: str
    email: EmailStr
    is_active: bool
    
    class Config:
        from_attributes = True

# Authentication functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {str(e)}")
        return False

def get_password_hash(password: str) -> str:
    """Generate a password hash."""
    try:
        return pwd_context.hash(password)
    except Exception as e:
        logger.error(f"Password hashing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing password"
        )

def authenticate_user(db: Session, username: str, password: str) -> Union[User, bool]:
    """Authenticate a user with username and password."""
    try:
        user = User.get_by_username(db, username)
        if not user:
            logger.warning(f"Authentication failed: User '{username}' not found")
            return False
        if not verify_password(password, user.hashed_password):
            logger.warning(f"Authentication failed: Invalid password for '{username}'")
            return False
        logger.info(f"User '{username}' authenticated successfully")
        return user
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        return False

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    try:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        logger.debug(f"Token created for user: {data.get('sub', 'unknown')}")
        return encoded_jwt
    except Exception as e:
        logger.error(f"Token creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating access token"
        )

def get_token_from_cookie(access_token: Optional[str] = Cookie(None)) -> Optional[str]:
    """Extract token from cookie."""
    if access_token and access_token.startswith("Bearer "):
        return access_token.replace("Bearer ", "")
    return None

def get_current_user(
    token: str = Depends(oauth2_scheme), 
    cookie_token: Optional[str] = Depends(get_token_from_cookie),
    db: Session = Depends(get_db)
) -> User:
    """Get the current user from the JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Try to use token from authorization header, fallback to cookie
    final_token = token or cookie_token
    if not final_token:
        logger.warning("Authentication failed: No token provided")
        raise credentials_exception
    
    try:
        payload = jwt.decode(final_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.warning("Authentication failed: Invalid token payload")
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError as e:
        logger.warning(f"JWT decode error: {str(e)}")
        raise credentials_exception
    
    try:
        user = User.get_by_username(db, username=token_data.username)
        if user is None:
            logger.warning(f"Authentication failed: User from token not found")
            raise credentials_exception
        logger.debug(f"User '{user.username}' authenticated via token")
        return user
    except Exception as e:
        logger.error(f"User lookup error: {str(e)}")
        raise credentials_exception

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get the current user and verify that they are active."""
    if not current_user.is_active:
        logger.warning(f"Access denied: User '{current_user.username}' is inactive")
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# User management functions
def create_user(db: Session, user: UserCreate) -> User:
    """Create a new user."""
    try:
        # Check if user already exists
        existing_email = User.get_by_email(db, user.email)
        if existing_email:
            logger.warning(f"User creation failed: Email '{user.email}' already registered")
            raise ValueError("Email already registered")
        
        existing_username = User.get_by_username(db, user.username)
        if existing_username:
            logger.warning(f"User creation failed: Username '{user.username}' already taken")
            raise ValueError("Username already taken")
        
        # Create new user
        db_user = User(
            username=user.username,
            email=user.email,
            hashed_password=get_password_hash(user.password)
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logger.info(f"User '{user.username}' created successfully")
        return db_user
    except ValueError as e:
        # Re-raise validation errors for the API
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user"
        )