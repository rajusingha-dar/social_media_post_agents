"""
LLM Engine module for generating and processing social media posts.
Enhanced with reflexion system that iteratively improves post quality.
"""

import logging
import os
from typing import Dict, List, Optional, Any

# Import from other modules
from .classify_prompt import get_classifier
from ..search.engine import query_search
from .post_generator import generate_platform_posts
from .critic_agent import refine_posts

from dotenv import load_dotenv
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

class LLMEngine:
    """
    Main engine for LLM-based post generation and processing.
    Complete pipeline with reflexion-based post improvement.
    """

    def __init__(self, openai_api_key=None, reflexion_iterations=5):
        """
        Initialize the LLM engine.
        
        Args:
            openai_api_key: API key for OpenAI (defaults to environment variable)
            reflexion_iterations: Number of improvement iterations for posts
        """
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        self.reflexion_iterations = reflexion_iterations
        logger.info(f"LLMEngine initialized with {reflexion_iterations} reflexion iterations")

    def generate_post_with_reflexion(self, prompt: str, platforms: list[str], verbose_reflexion=False) -> dict:
        """
        Generates social media posts with classification, search, and iterative refinement.
        
        Args:
            prompt: User's input prompt for post generation
            platforms: List of social media platforms to target
            verbose_reflexion: Whether to include detailed reflexion history
            
        Returns:
            Dictionary of platform-specific posts (and optional refinement data)
        """
        logger.info(f"Starting generation for prompt: {prompt}")
        try:
            # STEP 1: Classify the prompt topic using OpenAI
            classifier = get_classifier(api_key=self.openai_api_key)
            classification = classifier.classify(prompt)

            logger.info("Step 1 Complete: Prompt classified")
            print("classification----------->", classification)

            logger.debug(f"Prompt classified as: {classification['category']} with confidence {classification['confidence']}")
            logger.debug(f"User intent: {classification.get('intent')}")
            logger.debug(f"Subtopics: {classification.get('subtopics')}")
            logger.debug(f"Focus: {classification.get('focus')}")

            # STEP 2: Enhanced web search using classification data
            try:
                search_context = query_search(
                    prompt=prompt,
                    category=classification.get('category'),
                    subtopics=classification.get('subtopics'),
                    intent=classification.get('intent')
                )
                logger.info("Step 2 Complete: Search context retrieved")
                logger.debug(f"Search context length: {len(search_context)}")
            except Exception as search_error:
                logger.error(f"Search step failed: {search_error}")
                search_context = "Search data unavailable."

            # STEP 3: Generate initial platform-specific posts using search context
            try:
                initial_posts = generate_platform_posts(
                    prompt=prompt,
                    search_context=search_context,
                    platforms=platforms,
                    classification=classification
                )
                logger.info("Step 3 Complete: Initial platform-specific posts generated")
            except Exception as generation_error:
                logger.error(f"Post generation step failed: {generation_error}")
                # Fallback results
                initial_posts = {
                    platform: f"[{platform.capitalize()}] Post about {prompt} in the {classification.get('category', 'general')} category."
                    for platform in platforms
                }
                
            # STEP 4: Reflexion - iteratively improve posts with critic feedback
            try:
                logger.info(f"Step 4: Starting reflexion process with {self.reflexion_iterations} iterations")
                refined_results = refine_posts(
                    posts=initial_posts,
                    original_prompt=prompt,
                    search_context=search_context,
                    classification=classification,
                    max_iterations=self.reflexion_iterations,
                    verbose=verbose_reflexion
                )
                
                # Handle different return formats based on verbosity
                if verbose_reflexion:
                    final_posts = refined_results["posts"]
                    refinement_data = refined_results["refinement_data"]
                    logger.info("Step 4 Complete: Posts refined with detailed history")
                    
                    # Return both posts and refinement data
                    return {
                        "posts": final_posts,
                        "refinement_data": refinement_data
                    }
                else:
                    final_posts = refined_results
                    logger.info("Step 4 Complete: Posts refined")
                    
                    # Return just the posts
                    return final_posts
                    
            except Exception as reflexion_error:
                logger.error(f"Reflexion step failed: {reflexion_error}")
                # Fall back to initial posts if reflexion fails
                return initial_posts

        except Exception as e:
            logger.exception(f"Failed to generate post with reflexion: {str(e)}")
            results = {
                platform: f"[{platform.capitalize()}] Simple post about: {prompt}"
                for platform in platforms
            }
            return results


# Standalone function for backward compatibility
def generate_post_with_reflexion(prompt: str, platforms: list[str], reflexion_iterations=5, verbose_reflexion=False) -> dict:
    """
    Backward-compatible standalone function for the complete post generation pipeline.
    
    Args:
        prompt: User's input prompt for post generation
        platforms: List of social media platforms to target
        reflexion_iterations: Number of refinement iterations
        verbose_reflexion: Whether to include detailed reflexion history
        
    Returns:
        Dictionary of platform-specific posts (and optional refinement data)
    """
    engine = LLMEngine(reflexion_iterations=reflexion_iterations)
    return engine.generate_post_with_reflexion(prompt, platforms, verbose_reflexion)