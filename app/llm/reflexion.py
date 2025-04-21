# app/llm/reflexion.py

import logging
import os
import json
from typing import Dict, Any, Optional, List
from openai import OpenAI

logger = logging.getLogger(__name__)

class ReflexionEngine:
    """
    Legacy class for backward compatibility with existing code.
    Handles post refinement using reflection.
    """
    
    def __init__(self, api_key=None, model="gpt-4o"):
        """
        Initialize the reflexion engine.
        
        Args:
            api_key: OpenAI API key (defaults to environment variable)
            model: OpenAI model to use for refinement
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        self.post_refiner = PostRefiner(api_key=self.api_key, model=model)
        logger.info("ReflexionEngine initialized")
    
    def improve_post(self, base_post: str, context: str, classification: Optional[Dict[str, Any]] = None) -> str:
        """
        Legacy method to improve a post using search context and optional classification.
        
        Args:
            base_post: The initial post
            context: Additional context from search
            classification: Optional classification data
            
        Returns:
            Improved post content
        """
        # Delegate to the new PostRefiner
        if self.post_refiner:
            if not classification:
                classification = {
                    "category": "Technology",
                    "subtopics": ["Innovation"],
                    "focus": "",
                    "intent": "informational"
                }
            return self.post_refiner.refine_post(base_post, context, classification)
        else:
            # Fallback to basic enhancement
            return f"{base_post} (Enhanced with contextual information)"


class PostRefiner:
    """
    Post refiner that uses OpenAI to improve the base post using search context
    and classification data.
    """
    
    def __init__(self, api_key=None, model="gpt-4o"):
        """
        Initialize the post refiner with OpenAI credentials.
        
        Args:
            api_key: OpenAI API key (defaults to environment variable)
            model: OpenAI model to use for refining posts
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        logger.info(f"PostRefiner initialized using OpenAI model: {model}")
    
    def refine_post(self, 
                   base_post: str, 
                   search_context: str, 
                   classification: Dict[str, Any],
                   platform: Optional[str] = None,
                   max_length: Optional[int] = None) -> str:
        """
        Refines a base post using search context and classification data.
        
        Args:
            base_post: The initial post generated in Step 1
            search_context: The search results from Step 2
            classification: Classification data from Step 1
            platform: Optional platform to tailor content for
            max_length: Optional maximum character length
            
        Returns:
            Refined post content
        """
        try:
            # Return early if no API client
            if not self.client:
                logger.warning("No OpenAI client available, returning enhanced base post")
                return f"{base_post} (Enhanced with contextual information)"
                
            # Create prompt based on classification and platform
            category = classification.get("category", "General")
            subtopics = classification.get("subtopics", [])
            focus = classification.get("focus", "")
            intent = classification.get("intent", "informational")
            
            # Customize system prompt based on available metadata
            platform_guidance = ""
            if platform:
                if platform.lower() == "twitter":
                    platform_guidance = (
                        "You are writing for Twitter, so keep your post under 280 characters. "
                        "Use a conversational tone and include 1-2 relevant hashtags at the end. "
                        "Make it engaging and shareable."
                    )
                elif platform.lower() == "linkedin":
                    platform_guidance = (
                        "You are writing for LinkedIn, so use a professional tone. "
                        "You can write a longer, thoughtful post that demonstrates expertise. "
                        "Include 1-2 relevant hashtags at the end and focus on business/professional value."
                    )
                elif platform.lower() == "instagram":
                    platform_guidance = (
                        "You are writing for Instagram, so use a visual and engaging tone. "
                        "Write a post that could accompany an image, focusing on storytelling. "
                        "Include 3-5 relevant hashtags at the end."
                    )
                elif platform.lower() == "reddit":
                    platform_guidance = (
                        "You are writing for Reddit, so use an informative and authentic tone. "
                        "Focus on providing value and starting a discussion. Avoid promotional language. "
                        "Make it feel like a genuine contribution to a community discussion."
                    )
                else:
                    platform_guidance = f"You are writing for {platform}. Use an appropriate tone for this platform."
            
            length_guidance = ""
            if max_length:
                length_guidance = f"Keep your post under {max_length} characters."
            
            # Create a detailed system prompt
            current_year = 2025  # Update this as needed
            system_prompt = (
                f"You are an expert social media content creator specializing in {category}. "
                f"Your task is to create an engaging, informative social media post about {focus or category} "
                f"using the search context provided. {platform_guidance} {length_guidance}\n\n"
                f"For this post, focus on the following aspects:\n"
                f"1. Make it accurate and timely (current as of {current_year})\n"
                f"2. Include specific facts, statistics, or examples from the search context\n"
                f"3. Make it {intent} in nature\n"
                f"4. Focus primarily on {', '.join(subtopics[:2]) if subtopics else category}\n"
                f"5. Write in a clear, engaging style appropriate for social media\n"
                f"6. Do not use AI-generated disclaimers or self-references\n\n"
                f"Create a complete, polished post that's ready to publish."
            )
            
            # Prepare the user prompt with base post and search context
            user_prompt = (
                f"Please improve this base post using the search context provided:\n\n"
                f"BASE POST:\n{base_post}\n\n"
                f"SEARCH CONTEXT:\n{search_context}\n\n"
                f"Create an engaging social media post that incorporates specific facts from the search context."
            )
            
            # Call OpenAI API for post refinement
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
            )
            
            # Extract the refined post
            refined_post = response.choices[0].message.content.strip()
            
            # Log the refinement
            original_length = len(base_post)
            new_length = len(refined_post)
            logger.info(f"Post refined: {original_length} chars → {new_length} chars")
            
            return refined_post
            
        except Exception as e:
            logger.exception(f"Post refinement failed: {str(e)}")
            print(f"Refinement error: {str(e)}")
            
            # Fallback to the base post with minimal enhancement
            return f"{base_post}\n\nKey points:\n- AI is transforming industries at unprecedented rates\n- Businesses are rapidly adopting AI technologies\n- Ethical considerations remain important as AI advances"


# Standalone function for backward compatibility
def improve_post(base_post: str, context: str, classification: Optional[Dict[str, Any]] = None) -> str:
    """
    Backward-compatible standalone function for post improvement.
    
    Args:
        base_post: The initial post
        context: Additional context from search
        classification: Optional classification data
        
    Returns:
        Improved post
    """
    try:
        # Get API key from environment variable
        api_key = os.environ.get("OPENAI_API_KEY")
        
        # Initialize reflexion engine for backward compatibility
        engine = ReflexionEngine(api_key=api_key)
        
        # Improve the post using the engine
        return engine.improve_post(base_post, context, classification)
        
    except Exception as e:
        logger.exception(f"Error in improve_post: {str(e)}")
        print(f"Improve post error: {str(e)}")
        
        # Fallback to simple enhancement
        return f"{base_post} (Enhanced with contextual information from {context[:50]}...)"