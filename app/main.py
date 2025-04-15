# app/main.py
from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .database import get_db
from .auth import get_current_active_user, get_current_user
from .routes import auth_routes

app = FastAPI(title="AI Social Poster")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(auth_routes.router)

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Public landing page that doesn't require authentication"""
    return templates.TemplateResponse(
        "layout.html", 
        {"request": request, "user": None, "content": "Welcome to AI Social Poster! Please login or sign up to continue."}
    )

@app.get("/dashboard")
async def dashboard(request: Request, current_user=Depends(get_current_active_user)):
    """Dashboard page - Protected route that requires authentication"""
    return templates.TemplateResponse(
        "layout.html", 
        {"request": request, "user": current_user, "content": f"Welcome to your dashboard, {current_user.username}!"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)