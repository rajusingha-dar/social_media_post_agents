"""
Post Generator module for creating platform-specific social media content.
Uses OpenAI's LLM to generate authentic-sounding posts based on search results.
"""
import logging
import os
import json
from typing import Dict, List, Any, Optional
from openai import OpenAI

from dotenv import load_dotenv
load_dotenv()

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter("%Y-%m-%d %H:%M:%S - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

class PostGenerator:
    """
    Creates platform-specific social media posts using OpenAI and search context.
    """
    
    # Platform-specific characteristics
    PLATFORM_CONFIG = {
        "linkedin": {
            "tone": "professional",
            "max_length": 3000,
            "format": "paragraph",
            "hashtags_count": 3,
            "emoji_frequency": "low",
            "style": "include statistics and professional insights, use paragraphs, possibly with bullet points for clarity"
        },
        "twitter": {
            "tone": "conversational",
            "max_length": 280,
            "format": "concise",
            "hashtags_count": 2,
            "emoji_frequency": "medium",
            "style": "be concise, catchy, and engaging, possibly with a question or call to action"
        },
        "reddit": {
            "tone": "informative",
            "max_length": 10000,
            "format": "discussion",
            "hashtags_count": 0,
            "emoji_frequency": "very low",
            "style": "be informative and authentic, use clear formatting and cite your sources in an authentic way"
        },
        "instagram": {
            "tone": "casual",
            "max_length": 2200,
            "format": "engaging",
            "hashtags_count": 5,
            "emoji_frequency": "high",
            "style": "be engaging and visual, tell a story, and include many relevant hashtags at the end"
        },
        "facebook": {
            "tone": "friendly",
            "max_length": 5000,
            "format": "conversational",
            "hashtags_count": 1,
            "emoji_frequency": "medium",
            "style": "be personal and relatable, ask questions, and encourage engagement"
        }
    }
    
    def __init__(self, api_key=None, model="gpt-4o"):
        """
        Initialize the post generator.
        
        Args:
            api_key: OpenAI API key (defaults to environment variable)
            model: OpenAI model to use for generation
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        self.client = OpenAI(api_key=self.api_key)
        logger.info(f"PostGenerator initialized using OpenAI model: {model}")
    
    def generate_post(self, 
                      prompt: str,
                      search_context: str, 
                      platform: str,
                      classification: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a platform-specific post based on search context and classification.
        
        Args:
            prompt: Original user prompt
            search_context: Context from search results
            platform: Target platform (linkedin, twitter, reddit, etc.)
            classification: Optional classification data from Step 1
            
        Returns:
            Platform-appropriate post
        """
        try:
            # Get platform config
            platform = platform.lower()
            platform_config = self.PLATFORM_CONFIG.get(platform, self.PLATFORM_CONFIG["linkedin"])
            
            # Extract classification data if available
            category = "general"
            subtopics = []
            intent = "informational"
            
            if classification:
                category = classification.get("category", "general")
                subtopics = classification.get("subtopics", [])
                intent = classification.get("intent", "informational")
            
            # Create a hashtag suggestion based on classification
            hashtag_suggestions = ""
            if subtopics and platform_config["hashtags_count"] > 0:
                suggested_hashtags = [f"#{topic.replace(' ', '')}" for topic in subtopics[:platform_config["hashtags_count"]]]
                hashtag_suggestions = "Consider including these hashtags if relevant: " + ", ".join(suggested_hashtags)
            
            # Create system prompt that guides the post generation
            system_prompt = f"""
            You are an expert social media content creator who writes authentic, high-quality {platform} posts.
            
            When writing for {platform}, you:
            - Use a {platform_config['tone']} tone
            - Keep your posts under {platform_config['max_length']} characters
            - Format content in a {platform_config['format']} style
            - {platform_config['style']}
            
            For this post about {category}:
            1. Write in a natural human voice - avoid corporate or AI-sounding language
            2. Incorporate facts and statistics from the search context to add credibility
            3. Don't reveal that you're an AI or that the post is AI-generated
            4. Focus on the user's original request
            5. Make the content feel authentic and native to {platform}
            6. Match the natural writing style of a real person with expertise in this topic
            
            {hashtag_suggestions}
            
            Don't include platform-specific formatting like "[Twitter]" or "[LinkedIn]" - just write the post content itself.
            """
            
            # User prompt combines the original request and search context
            user_prompt = f"""
            Original request: {prompt}
            
            SEARCH CONTEXT:
            {search_context}
            
            Create an authentic, engaging {platform} post using this information.
            """
            
            # Get completion from OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.8,  # Slightly higher for creativity
                max_tokens=1000,
                frequency_penalty=0.7,  # Encourage more variation in language
                presence_penalty=0.6    # Encourage covering different topics
            )
            
            # Extract the generated post
            post_content = response.choices[0].message.content.strip()
            
            # Log success
            logger.info(f"Successfully generated {platform} post")
            
            return post_content
            
        except Exception as e:
            logger.exception(f"Error generating post for {platform}: {str(e)}")
            # Fallback post if generation fails
            return f"Check out the latest information about {prompt}! Very interesting developments happening in this space."

def generate_platform_posts(prompt: str, search_context: str, platforms: List[str], classification: Optional[Dict] = None) -> Dict[str, str]:
    """
    Generate posts for multiple platforms.
    
    Args:
        prompt: Original user prompt
        search_context: Search results
        platforms: List of target platforms
        classification: Optional classification data
        
    Returns:
        Dictionary of platform -> post content
    """
    try:
        # Initialize post generator
        api_key = os.environ.get("OPENAI_API_KEY")
        generator = PostGenerator(api_key=api_key)
        
        # Generate posts for each platform
        results = {}
        for platform in platforms:
            post = generator.generate_post(
                prompt=prompt,
                search_context=search_context,
                platform=platform,
                classification=classification
            )
            
            # Add platform name as prefix to the post
            results[platform] = f"[{platform.capitalize()}] {post}"
        
        return results
        
    except Exception as e:
        logger.exception(f"Error in generate_platform_posts: {str(e)}")
        # Fallback results
        return {platform: f"[{platform.capitalize()}] Post about {prompt}" for platform in platforms}