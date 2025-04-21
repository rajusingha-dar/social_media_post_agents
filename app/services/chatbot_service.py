# app/services/chatbot_service.py
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from ..models.chat import Conversation, Message
from ..models.post import SocialMediaPost, PlatformType
from ..llm.engine import LLMEngine
from ..llm.reflexion import ReflexionEngine
from ..search.engine import SearchEngine
from ..llm.prompts import INITIAL_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)

class ChatbotService:
    def __init__(self):
        self.llm_engine = LLMEngine()
        self.reflexion_engine = ReflexionEngine(self.llm_engine)
        self.search_engine = SearchEngine()
        logger.info("Chatbot Service initialized")
    
    async def start_conversation(self, db: Session, user_id: int) -> Conversation:
        """Start a new conversation for a user."""
        try:
            conversation = Conversation(user_id=user_id)
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            logger.info(f"Started new conversation {conversation.id} for user {user_id}")
            return conversation
        except Exception as e:
            db.rollback()
            logger.error(f"Error starting conversation: {str(e)}")
            raise
    
    async def process_message(self, 
                       db: Session, 
                       conversation_id: int, 
                       user_id: int, 
                       content: str, 
                       platforms: List[str]) -> Dict[str, Any]:
        """Process a user message and generate appropriate responses and posts."""
        try:
            logger.info(f"Processing message for conversation {conversation_id}")
            
            # Save the user message
            user_message = Message(
                conversation_id=conversation_id,
                role="user",
                content=content
            )
            db.add(user_message)
            
            # Perform web search for relevant information
            search_results = await self.search_engine.search(content)
            search_context = "\n\n".join([
                f"Source: {result['title']}\nURL: {result['url']}\nExcerpt: {result['snippet']}"
                for result in search_results
            ])
            
            # Create messages list for conversation history
            messages = [
                {"role": "system", "content": INITIAL_PROMPT_TEMPLATE.format(
                    platforms=", ".join(platforms),
                    search_results=search_context
                )},
                {"role": "user", "content": content}
            ]
            
            # Generate initial response
            initial_response = await self.llm_engine.generate_response(messages)
            
            # Save the assistant response
            assistant_message = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=initial_response
            )
            db.add(assistant_message)
            
            # Process each platform
            post_results = {}
            for platform in platforms:
                # Generate platform-specific content
                platform_content = await self.reflexion_engine.refine_content(
                    platform=platform,
                    original_prompt=content,
                    current_content=initial_response
                )
                
                # Create a post record
                post = SocialMediaPost(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    platform=platform,
                    content=platform_content,
                    draft_versions={"1": platform_content}
                )
                db.add(post)
                
                post_results[platform] = platform_content
            
            db.commit()
            logger.info(f"Successfully processed message for conversation {conversation_id}")
            
            return {
                "response": initial_response,
                "posts": post_results
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Error processing message: {str(e)}")
            raise
    
    async def refine_post(self, 
                    db: Session, 
                    post_id: int, 
                    user_feedback: str) -> SocialMediaPost:
        """Refine a post based on user feedback."""
        try:
            logger.info(f"Refining post {post_id} with user feedback")
            
            # Get the post
            post = db.query(SocialMediaPost).filter(SocialMediaPost.id == post_id).first()
            if not post:
                logger.error(f"Post {post_id} not found")
                raise ValueError(f"Post {post_id} not found")
            
            # Get the conversation
            conversation = db.query(Conversation).filter(Conversation.id == post.conversation_id).first()
            if not conversation:
                logger.error(f"Conversation {post.conversation_id} not found")
                raise ValueError(f"Conversation {post.conversation_id} not found")
            
            # Get the original request
            original_request = None
            for message in db.query(Message).filter(
                Message.conversation_id == conversation.id,
                Message.role == "user"
            ).order_by(Message.created_at.asc()).limit(1):
                original_request = message.content
            
            if not original_request:
                logger.error(f"Original request not found for conversation {conversation.id}")
                raise ValueError(f"Original request not found")
            
            # Save feedback as a message
            feedback_message = Message(
                conversation_id=conversation.id,
                role="user",
                content=f"Feedback on {post.platform} post: {user_feedback}"
            )
            db.add(feedback_message)
            
            # Create messages for refinement
            messages = [
                {"role": "system", "content": f"You are a professional {post.platform} content writer. Refine the post based on user feedback."},
                {"role": "user", "content": f"Original request: {original_request}"},
                {"role": "assistant", "content": post.content},
                {"role": "user", "content": f"Please refine this post based on my feedback: {user_feedback}"}
            ]
            
            # Generate refined content
            refined_content = await self.llm_engine.generate_response(messages)
            
            # Save assistant response
            assistant_message = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=f"Refined {post.platform} post: {refined_content}"
            )
            db.add(assistant_message)
            
            # Update post content and draft versions
            draft_versions = post.draft_versions or {}
            new_version_num = str(len(draft_versions) + 1)
            draft_versions[new_version_num] = refined_content
            
            post.content = refined_content
            post.draft_versions = draft_versions
            
            db.commit()
            db.refresh(post)
            
            logger.info(f"Successfully refined post {post_id}")
            return post
        except Exception as e:
            db.rollback()
            logger.error(f"Error refining post: {str(e)}")
            raise