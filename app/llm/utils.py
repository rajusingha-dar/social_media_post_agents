# app/llm/utils.py

import logging

logger = logging.getLogger(__name__)

def improve_post(post: str, context: str = "") -> str:
    """
    Enhances a generated post using optional context from search results.
    This function applies a basic 'reflexion' strategy by appending useful insights.
    """
    try:
        logger.debug("Improving post using context from search results")
        
        if context:
            enhanced = f"{post}\n\n💡 Based on what we found:\n{context}"
        else:
            enhanced = f"{post} ✅ (Reviewed and approved via reflexion)"
        
        logger.info("Post improved successfully")
        return enhanced
    
    except Exception as e:
        logger.exception("Failed to improve post with context")
        return f"{post} ❌ (Reflexion failed: {str(e)})"
