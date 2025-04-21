# app/main.py
import logging
import os
from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .database import get_db, initialize_db
from .auth import get_current_active_user, get_current_user
from .routes import auth_routes
from .config import settings




# app/main.py
import logging
from fastapi import FastAPI, Depends, Request, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

# Import database components first
from .database import get_db, initialize_db

# Import models to ensure they're registered with SQLAlchemy
from .models.chat import Conversation, Message
from .models.post import SocialMediaPost, PlatformType

# Import auth components
from .auth import get_current_active_user, get_current_user

# Import route modules
from .routes import auth_routes

from .database import Base, engine
from .models import *  # This will import all models from __init__.py

# Your existing main.py code follows...

# Configure root logger
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="AI Social Poster",
    description="Generate social media content using AI",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize templates
try:
    templates = Jinja2Templates(directory="templates")
    logger.info("Template engine initialized")
except Exception as e:
    logger.error(f"Failed to initialize templates: {str(e)}")
    raise

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
    logger.info("Static files mounted at /static")
except Exception as e:
    logger.error(f"Failed to mount static files: {str(e)}")
    # Continue without static files, application will work but without styles

# Exception handler for all HTTP exceptions
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        logger.warning(f"404 Not Found: {request.url}")
        # Return custom 404 page
        return templates.TemplateResponse(
            "error.html", 
            {"request": request, "error": "Page not found", "status_code": 404},
            status_code=404
        )
    elif exc.status_code == 401:
        logger.warning(f"401 Unauthorized: {request.url}")
        # Redirect to login for unauthorized access
        return templates.TemplateResponse(
            "error.html", 
            {"request": request, "error": "Please log in to access this page", "status_code": 401},
            status_code=401
        )
    
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return templates.TemplateResponse(
        "error.html", 
        {"request": request, "error": exc.detail, "status_code": exc.status_code},
        status_code=exc.status_code
    )

# Exception handler for general exceptions
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return templates.TemplateResponse(
        "error.html", 
        {"request": request, "error": "An unexpected error occurred", "status_code": 500},
        status_code=500
    )

# Include routers
try:
    app.include_router(auth_routes.router)
    logger.info("Authentication routes registered")
except Exception as e:
    logger.error(f"Failed to register auth routes: {str(e)}")
    raise

@app.on_event("startup")
async def startup_event():
    """Application startup: initialize database and other resources."""
    try:
        # Initialize database
        initialize_db()
        logger.info("Application startup complete")
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        # We allow the app to start even if DB init fails
        # This way the app can display a maintenance page

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Public landing page that doesn't require authentication."""
    try:
        logger.debug("Landing page requested")
        return templates.TemplateResponse(
            "layout.html", 
            {"request": request, "user": None, "content": "Welcome to AI Social Poster! Please login or sign up to continue."}
        )
    except Exception as e:
        logger.error(f"Error rendering landing page: {str(e)}")
        return HTMLResponse(content="<html><body><h1>Error loading page</h1><p>Please try again later.</p></body></html>")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, current_user=Depends(get_current_active_user)):
    """Dashboard page - Protected route that requires authentication."""
    try:
        logger.debug(f"Dashboard requested by user: {current_user.username}")
        return templates.TemplateResponse(
            "dashboard.html", 
            {"request": request, "user": current_user}
        )
    except Exception as e:
        logger.error(f"Error rendering dashboard: {str(e)}")
        return templates.TemplateResponse(
            "error.html", 
            {"request": request, "error": "Error loading dashboard", "status_code": 500},
            status_code=500
        )

@app.get("/create-post", response_class=HTMLResponse)
async def create_post_page(request: Request, current_user=Depends(get_current_active_user)):
    """Create post page - Protected route that requires authentication."""
    try:
        logger.debug(f"Create post page requested by user: {current_user.username}")
        return templates.TemplateResponse(
            "create_post.html", 
            {"request": request, "user": current_user}
        )
    except Exception as e:
        logger.error(f"Error rendering create post page: {str(e)}")
        return templates.TemplateResponse(
            "error.html", 
            {"request": request, "error": "Error loading create post page", "status_code": 500},
            status_code=500
        )

@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request, current_user=Depends(get_current_active_user)):
    """User profile page - Protected route that requires authentication."""
    try:
        logger.debug(f"Profile page requested by user: {current_user.username}")
        return templates.TemplateResponse(
            "profile.html", 
            {"request": request, "user": current_user}
        )
    except Exception as e:
        logger.error(f"Error rendering profile page: {str(e)}")
        return templates.TemplateResponse(
            "error.html", 
            {"request": request, "error": "Error loading profile page", "status_code": 500},
            status_code=500
        )

if __name__ == "__main__":
    import uvicorn
    
    # Note: It's generally better to run with the uvicorn command directly
    # rather than using this block, but it's included for convenience
    try:
        logger.info("Starting application via __main__ block")
        uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")



@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with a custom error page or fallback"""
    try:
        # Try to use the custom error.html template
        return templates.TemplateResponse(
            "error.html", 
            {"request": request, "error": exc.detail, "status_code": exc.status_code},
            status_code=exc.status_code
        )
    except Exception as e:
        # Fallback to a simple error response if template is missing
        logger.error(f"Error rendering error template: {str(e)}")
        if exc.status_code == 404:
            content = "<html><body><h1>404 - Page Not Found</h1><p>The page you requested does not exist.</p></body></html>"
        elif exc.status_code == 401:
            content = "<html><body><h1>401 - Unauthorized</h1><p>Please log in to continue.</p></body></html>"
        else:
            content = f"<html><body><h1>Error {exc.status_code}</h1><p>{exc.detail}</p></body></html>"
        return HTMLResponse(content=content, status_code=exc.status_code)

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with a custom error page or fallback"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    try:
        # Try to use the custom error.html template
        return templates.TemplateResponse(
            "error.html", 
            {"request": request, "error": "An unexpected error occurred", "status_code": 500},
            status_code=500
        )
    except Exception as e:
        # Fallback to a simple error response if template is missing
        logger.error(f"Error rendering error template: {str(e)}")
        content = "<html><body><h1>500 - Server Error</h1><p>An unexpected error occurred. Please try again later.</p></body></html>"
        return HTMLResponse(content=content, status_code=500)
    


# app/main.py (update to include new routes)
from .routes import chatbot_routes

# Existing code...

# Include chatbot routers
app.include_router(chatbot_routes.router)
logger.info("Chatbot routes registered")

# Redirect authenticated users to chatbot
@app.get("/dashboard")
async def dashboard(request: Request, current_user=Depends(get_current_active_user)):
    """Dashboard - redirects to chatbot for authenticated users"""
    return RedirectResponse(url="/chatbot", status_code=status.HTTP_303_SEE_OTHER)


from app.routes import chatbot_routes
app.include_router(chatbot_routes.router)