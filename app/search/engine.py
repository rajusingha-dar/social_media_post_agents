import logging
import os
import json
from typing import List, Dict, Any, Optional
from openai import OpenAI

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter("%Y-%m-%d %H:%M:%S - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

class SearchEngine:
    def __init__(self, api_key=None, model="gpt-4o"):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        self.client = OpenAI(api_key=self.api_key)
        logger.info(f"Search Engine initialized using OpenAI model: {model}")

    def search(self, query: str, category: Optional[str] = None, 
               subtopics: Optional[List[str]] = None, 
               intent: Optional[str] = None,
               num_results: int = 5) -> Dict[str, Any]:

        try:
            enhanced_query = query
            if category:
                enhanced_query = f"{category}: {query}"
            if subtopics:
                subtopics_str = ", ".join(subtopics[:3])
                enhanced_query += f" (focusing on {subtopics_str})"
            if intent:
                enhanced_query += f" | Intent: {intent}"

            logger.info(f"Running enhanced search for: {enhanced_query}")

            current_year = 2025
            system_prompt = (
                f"You are a web search expert with access to the latest information as of {current_year}. "
                f"Given a query about {category or 'a topic'}, provide {num_results} distinct, factual, and recent pieces of information.\n"
                f"Return as JSON with an array called 'results', each having 'fact' and 'source'."
            )

            # Only change: Fixed the response_format to be a dict instead of string
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Search query: {enhanced_query}"}
                ],
                temperature=0.5,
                response_format={"type": "json_object"}  # Changed from "json_object" string
            )

            content = response.choices[0].message.content
            logger.debug("Search response received")

            # 🔍 Print raw search output for verification
            print("\n🔎 [Search Agent Output Preview]")
            print(content[:1000])
            print("🔍 End of Search Output\n")

            try:
                results_data = json.loads(content)
                items = results_data.get("results") or []
                return {
                    "original_query": query,
                    "enhanced_query": enhanced_query,
                    "category": category,
                    "results": {"items": items},
                    "timestamp": "2025-04-21"
                }

            except json.JSONDecodeError as e:
                logger.warning(f"JSON decode error: {str(e)}")
                return {
                    "original_query": query,
                    "enhanced_query": enhanced_query,
                    "category": category,
                    "results": {"items": [{"fact": content, "source": "OpenAI"}]},
                    "timestamp": "2025-04-21"
                }

        except Exception as e:
            logger.exception(f"Search via OpenAI failed: {str(e)}")
            return {
                "original_query": query,
                "enhanced_query": query,
                "category": category,
                "results": {"items": self._get_fallback_results(category)},
                "timestamp": "2025-04-21"
            }

    def _get_fallback_results(self, category: Optional[str] = None) -> List[Dict[str, str]]:
        return [{"fact": f"Fallback info for {category or 'Technology'}.", "source": "Fallback DB"}]

    def format_search_context(self, search_results: Dict[str, Any]) -> str:
        context_parts = [
            f"SEARCH CONTEXT FOR: {search_results.get('enhanced_query')}",
            f"CATEGORY: {search_results.get('category')}",
            f"DATE: {search_results.get('timestamp')}\n"
        ]

        items = search_results.get("results", {}).get("items", [])

        for i, item in enumerate(items, 1):
            fact = item.get("fact", "Unknown")
            source = item.get("source", "Unknown")
            context_parts.append(f"{i}. {fact}\n   Source: {source}\n")

        return "\n".join(context_parts)

def query_search(prompt: str, category: Optional[str] = None, subtopics: Optional[List[str]] = None, intent: Optional[str] = None) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    engine = SearchEngine(api_key=api_key)
    search_results = engine.search(prompt, category, subtopics, intent)
    print("search_results-------------------->", search_results)
    return engine.format_search_context(search_results)

def simple_query_search(prompt: str, category: Optional[str] = None) -> str:
    engine = SearchEngine()
    fallback_items = engine._get_fallback_results(category)
    return "\n".join(f"{i+1}. {item['fact']}\n   Source: {item['source']}" for i, item in enumerate(fallback_items))