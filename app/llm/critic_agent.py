"""
Critic Agent module for evaluating and suggesting improvements for social media posts.
Uses OpenAI to provide insightful feedback to refine content quality.
"""
import logging
import os
from typing import Dict, Any, List, Tuple
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

class CriticAgent:
    """
    Evaluates social media posts and provides specific feedback for improvement.
    Works as a reflexion mechanism to iteratively enhance post quality.
    """
    
    def __init__(self, api_key=None, model="gpt-4o"):
        """
        Initialize the critic agent.
        
        Args:
            api_key: OpenAI API key (defaults to environment variable)
            model: OpenAI model to use for evaluation
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        self.client = OpenAI(api_key=self.api_key)
        logger.info(f"CriticAgent initialized using OpenAI model: {model}")
    
    def evaluate_post(self, 
                      post: str, 
                      platform: str, 
                      original_prompt: str,
                      search_context: str,
                      iteration: int,
                      classification: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Evaluate a social media post and provide specific feedback.
        
        Args:
            post: The social media post to evaluate
            platform: Target platform (linkedin, twitter, etc.)
            original_prompt: User's original request
            search_context: Search results used for post generation
            iteration: Current iteration number
            classification: Classification data from Step 1
            
        Returns:
            Dictionary with score, feedback, and improvement suggestions
        """
        try:
            # Extract relevant classification data if available
            category = "general topic"
            intent = "informative"
            
            if classification:
                category = classification.get("category", "general topic")
                intent = classification.get("intent", "informative")
            
            # Create system prompt for the critic
            system_prompt = f"""
            You are an expert social media critic who evaluates posts for {platform} and provides specific, actionable feedback.
            
            For iteration {iteration}/5, you'll evaluate a {platform} post about {category} and identify opportunities for improvement.
            
            When evaluating, consider:
            1. Content relevance: Does it address the original prompt?
            2. Platform suitability: Is it formatted appropriately for {platform}?
            3. Engagement potential: Will it resonate with the target audience?
            4. Factual accuracy: Does it correctly incorporate information from the search context?
            5. Authenticity: Does it sound natural and human-written?
            6. Clarity: Is the message clear and well-structured?
            
            Provide your evaluation in JSON format with these fields:
            - score: Numerical rating from 1-10
            - strengths: List of specific strengths
            - weaknesses: List of specific weaknesses
            - improvement_suggestions: Specific, actionable suggestions to improve the post
            - improved_version: A rewritten version that addresses your feedback
            
            Be specific and constructive in your feedback. For the improved_version, create a genuinely better post that addresses all the weaknesses.
            """
            
            # User prompt combines all context
            user_prompt = f"""
            Original request: {original_prompt}
            
            SEARCH CONTEXT:
            {search_context}
            
            POST TO EVALUATE ({platform}):
            {post}
            
            Please evaluate this post and suggest improvements while keeping the overall message intact.
            """
            
            # Get evaluation from OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.5,
            )
            
            # Extract and parse the evaluation
            content = response.choices[0].message.content
            
            # Debug output
            logger.debug(f"Raw critique response: {content[:500]}...")
            
            # Parse JSON response
            import json
            evaluation = json.loads(content)
            
            # Ensure all required fields are present
            evaluation.setdefault("score", 5)
            evaluation.setdefault("strengths", [])
            evaluation.setdefault("weaknesses", [])
            evaluation.setdefault("improvement_suggestions", [])
            evaluation.setdefault("improved_version", post)  # Default to original if missing
            
            # Add iteration info
            evaluation["iteration"] = iteration
            
            return evaluation
            
        except Exception as e:
            logger.exception(f"Error evaluating post: {str(e)}")
            # Return basic feedback if evaluation fails
            return {
                "score": 5,
                "strengths": ["Contains relevant information"],
                "weaknesses": ["Could be more engaging"],
                "improvement_suggestions": ["Add more specific details"],
                "improved_version": post,  # Return original post
                "iteration": iteration
            }

class ReflexionEngine:
    """
    Manages the reflexion process through multiple iterations of critique and improvement.
    """
    
    def __init__(self, api_key=None, max_iterations=5):
        """
        Initialize the reflexion engine.
        
        Args:
            api_key: OpenAI API key (defaults to environment variable)
            max_iterations: Maximum number of improvement iterations
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.max_iterations = max_iterations
        self.critic = CriticAgent(api_key=self.api_key)
        logger.info(f"ReflexionEngine initialized with {max_iterations} max iterations")
    
    def refine_post(self, 
                    initial_post: str, 
                    platform: str, 
                    original_prompt: str,
                    search_context: str,
                    classification: Dict[str, Any] = None,
                    verbose: bool = False) -> Dict[str, Any]:
        """
        Refine a post through multiple iterations of critique and improvement.
        
        Args:
            initial_post: Initial generated post
            platform: Target social media platform
            original_prompt: User's original request
            search_context: Search results for context
            classification: Classification data from Step 1
            verbose: Whether to return detailed history or just final post
            
        Returns:
            Dictionary with final post and optional history
        """
        current_post = initial_post
        iteration_history = []
        
        # Remove platform prefix if present
        if current_post.startswith(f"[{platform.capitalize()}] "):
            current_post = current_post[len(f"[{platform.capitalize()}] "):]
        
        logger.info(f"Starting reflexion process for {platform} post with {self.max_iterations} iterations")
        
        # Iterate through refinement process
        for i in range(1, self.max_iterations + 1):
            logger.info(f"Reflexion iteration {i}/{self.max_iterations}")
            
            # Get critique and suggestions
            evaluation = self.critic.evaluate_post(
                post=current_post,
                platform=platform,
                original_prompt=original_prompt,
                search_context=search_context,
                iteration=i,
                classification=classification
            )
            
            # Store iteration data
            iteration_data = {
                "iteration": i,
                "post": current_post,
                "score": evaluation.get("score", 0),
                "strengths": evaluation.get("strengths", []),
                "weaknesses": evaluation.get("weaknesses", []),
                "suggestions": evaluation.get("improvement_suggestions", [])
            }
            iteration_history.append(iteration_data)
            
            # Log evaluation summary
            logger.info(f"Iteration {i} score: {evaluation.get('score', 0)}/10")
            
            # Update the post with improved version
            improved_version = evaluation.get("improved_version", current_post)
            if improved_version and len(improved_version) > 10:  # Basic validation
                current_post = improved_version
            
            # Early stopping if we've reached a high score
            if evaluation.get("score", 0) >= 9:
                logger.info(f"Reached high quality score ({evaluation.get('score', 0)}). Early stopping.")
                break
        
        # Prepare the result
        final_post = f"[{platform.capitalize()}] {current_post}"
        
        result = {
            "final_post": final_post,
            "platform": platform,
            "iterations_completed": len(iteration_history),
            "final_score": iteration_history[-1]["score"] if iteration_history else 0
        }
        
        # Include detailed history if verbose
        if verbose:
            result["iteration_history"] = iteration_history
        
        return result

# Standalone helper function
def refine_posts(posts: Dict[str, str], 
                 original_prompt: str,
                 search_context: str,
                 classification: Dict[str, Any] = None,
                 max_iterations: int = 5,
                 verbose: bool = False) -> Dict[str, Any]:
    """
    Refine multiple posts with the reflexion engine.
    
    Args:
        posts: Dictionary of platform -> post content
        original_prompt: User's original request
        search_context: Search context from Step 2
        classification: Classification data from Step 1
        max_iterations: Maximum refinement iterations
        verbose: Whether to return detailed history
        
    Returns:
        Dictionary of refined posts with optional history
    """
    try:
        # Initialize engine
        api_key = os.environ.get("OPENAI_API_KEY")
        engine = ReflexionEngine(api_key=api_key, max_iterations=max_iterations)
        
        # Refine each post
        refined_posts = {}
        refinement_data = {}
        
        for platform, post in posts.items():
            logger.info(f"Refining post for {platform}")
            
            result = engine.refine_post(
                initial_post=post,
                platform=platform,
                original_prompt=original_prompt,
                search_context=search_context,
                classification=classification,
                verbose=verbose
            )
            
            # Store the final post
            refined_posts[platform] = result["final_post"]
            
            # Store detailed refinement data if verbose
            if verbose:
                refinement_data[platform] = result
        
        # Return appropriate results based on verbosity
        if verbose:
            return {
                "posts": refined_posts,
                "refinement_data": refinement_data
            }
        else:
            return refined_posts
            
    except Exception as e:
        logger.exception(f"Error in refine_posts: {str(e)}")
        # Return original posts if refinement fails
        return posts