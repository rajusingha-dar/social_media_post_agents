import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status, Cookie
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from ..database import get_db
from ..models.user import User
from ..services.chatbot_service import ChatbotService
from ..auth import get_token_from_cookie, get_user_from_token, get_current_active_user
from app.llm.engine import generate_post_with_reflexion

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="templates")
chatbot_service = ChatbotService()

class MessageRequest(BaseModel):
    content: str
    platforms: List[str]

class FeedbackRequest(BaseModel):
    feedback: str

@router.get("/chatbot", response_class=HTMLResponse)
async def chatbot_page(
    request: Request,
    token: Optional[str] = Depends(get_token_from_cookie),
    db: Session = Depends(get_db)
):
    try:
        if not token:
            logger.warning("No authentication token found in cookie")
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "error": "Not authenticated", "status_code": 401,
                 "message": "You need to be logged in to access this page."}
            )

        current_user = get_user_from_token(db, token)
        if not current_user:
            logger.warning("Invalid authentication token")
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "error": "Invalid authentication", "status_code": 401,
                 "message": "Your session is invalid or expired. Please log in again."}
            )

        logger.info(f"User {current_user.username} accessed chatbot page")
        return templates.TemplateResponse("chatbot.html", {"request": request, "user": current_user})
    except Exception as e:
        logger.error(f"Error rendering chatbot page: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": "Server error", "status_code": 500,
             "message": "An error occurred while loading the chatbot interface."}
        )

@router.post("/api/generate")
async def generate_post(
    message: MessageRequest,
    token: Optional[str] = Depends(get_token_from_cookie),
    db: Session = Depends(get_db)
):
    current_user = get_user_from_token(db, token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Invalid or missing token")

    try:
        logger.info(f"Generating post for user {current_user.username}")
        print("message.content", message.content)
        print("message.platforms", message.platforms)
        result = generate_post_with_reflexion(message.content, message.platforms)
        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Error generating post: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate post")
