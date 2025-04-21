# app/routes/auth_routes.py
import logging
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Form
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pydantic import EmailStr


from ..database import get_db
from ..models.user import User

from ..auth import (
    authenticate_user, create_access_token, 
    get_current_active_user, create_user,
    ACCESS_TOKEN_EXPIRE_MINUTES, UserCreate, Token, UserResponse
)
from ..config import settings

# Configure module logger
logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# API routes for authentication
@router.post("/api/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """API endpoint for token-based authentication."""
    try:
        logger.info(f"API login attempt for user: {form_data.username}")
        user = authenticate_user(db, form_data.username, form_data.password)
        if not user:
            logger.warning(f"API login failed for user: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        logger.info(f"API login successful for user: {form_data.username}")
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error in token generation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error"
        )

@router.post("/api/register", response_model=UserResponse)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """API endpoint for user registration."""
    try:
        logger.info(f"API registration attempt for user: {user.username}")
        
        # Check if email exists
        db_user_by_email = User.get_by_email(db, email=user.email)
        if db_user_by_email:
            logger.warning(f"API registration failed: Email {user.email} already registered")
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Check if username exists
        db_user_by_username = User.get_by_username(db, username=user.username)
        if db_user_by_username:
            logger.warning(f"API registration failed: Username {user.username} already taken")
            raise HTTPException(status_code=400, detail="Username already taken")
        
        # Create the user
        new_user = create_user(db=db, user=user)
        logger.info(f"API registration successful for user: {user.username}")
        return new_user
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error in user registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration error"
        )

@router.get("/api/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """API endpoint to get current user's information."""
    try:
        logger.debug(f"User info requested for: {current_user.username}")
        return current_user
    except Exception as e:
        logger.error(f"Error retrieving user info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user information"
        )

# Web routes for authentication
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render the login page."""
    try:
        logger.debug("Login page requested")
        return templates.TemplateResponse("login.html", {"request": request})
    except Exception as e:
        logger.error(f"Error rendering login page: {str(e)}")
        # Fallback to a simple error page
        return HTMLResponse(content="<html><body><h1>Error loading login page</h1></body></html>")

@router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    """Render the signup page."""
    try:
        logger.debug("Signup page requested")
        return templates.TemplateResponse("signup.html", {"request": request})
    except Exception as e:
        logger.error(f"Error rendering signup page: {str(e)}")
        # Fallback to a simple error page
        return HTMLResponse(content="<html><body><h1>Error loading signup page</h1></body></html>")

@router.get("/logout", response_class=HTMLResponse)
async def logout_page(request: Request):
    """Render the logout confirmation page."""
    try:
        logger.debug("Logout page requested")
        return templates.TemplateResponse("logout.html", {"request": request})
    except Exception as e:
        logger.error(f"Error rendering logout page: {str(e)}")
        # Fallback to a direct logout
        response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
        response.delete_cookie(key="access_token")
        return response

@router.post("/login")
async def login_form(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Handle login form submission."""
    try:
        logger.info(f"Web login attempt for user: {username}")
        user = authenticate_user(db, username, password)
        
        if not user:
            logger.warning(f"Web login failed for user: {username}")
            return templates.TemplateResponse(
                "login.html", 
                {"request": request, "error": "Invalid username or password"}
            )
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        # Changed the redirect URL from "/" to "/chatbot"
        response = RedirectResponse(url="/chatbot", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(
            key="access_token", 
            value=f"Bearer {access_token}", 
            httponly=True,
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            samesite="lax"
        )
        logger.info(f"Web login successful for user: {username}")
        return response
    except Exception as e:
        logger.error(f"Error processing login form: {str(e)}")
        return templates.TemplateResponse(
            "login.html", 
            {"request": request, "error": "An error occurred during login. Please try again."}
        )

@router.post("/signup")
async def signup_form(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Handle signup form submission."""
    try:
        logger.info(f"Web signup attempt for user: {username}")
        
        # Validate inputs
        if len(username) < 3:
            return templates.TemplateResponse(
                "signup.html", 
                {"request": request, "error": "Username must be at least 3 characters"}
            )
        
        if len(password) < 8:
            return templates.TemplateResponse(
                "signup.html", 
                {"request": request, "error": "Password must be at least 8 characters"}
            )
        
        # Check if email exists
        if User.get_by_email(db, email):
            logger.warning(f"Web signup failed: Email {email} already registered")
            return templates.TemplateResponse(
                "signup.html", 
                {"request": request, "error": "Email already registered"}
            )
        
        # Check if username exists
        if User.get_by_username(db, username):
            logger.warning(f"Web signup failed: Username {username} already taken")
            return templates.TemplateResponse(
                "signup.html", 
                {"request": request, "error": "Username already taken"}
            )
        
        # Create the user
        user_data = UserCreate(username=username, email=email, password=password)
        create_user(db=db, user=user_data)
        
        logger.info(f"Web signup successful for user: {username}")
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as he:
        logger.warning(f"Web signup failed for user {username}: {str(he)}")
        return templates.TemplateResponse(
            "signup.html", 
            {"request": request, "error": he.detail}
        )
    except Exception as e:
        logger.error(f"Error processing signup form: {str(e)}")
        return templates.TemplateResponse(
            "signup.html", 
            {"request": request, "error": "An error occurred during signup. Please try again."}
        )

@router.post("/logout")
async def logout_form(response: Response):
    """Handle logout form submission."""
    try:
        logger.info("User logged out")
        response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
        response.delete_cookie(key="access_token")
        return response
    except Exception as e:
        logger.error(f"Error processing logout: {str(e)}")
        # Still try to logout even if there's an error
        response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
        response.delete_cookie(key="access_token")
        return response