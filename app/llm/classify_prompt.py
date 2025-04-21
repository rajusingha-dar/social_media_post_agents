import logging
import openai
from typing import Dict

# Logger configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

CLASSIFICATION_PROMPT = """
You are a smart classifier agent. 
Given a prompt, classify the following details in structured JSON format:
1. category: General category of the topic (e.g., Technology, Health, Business, Education, Sports, etc.)
2. intent: User's intent behind the prompt (e.g., Inform, Entertain, Promote, Ask, Inspire, Educate, Alert)
3. subtopics: List of related subtopics (max 3)
4. focus: The specific angle or focus of the prompt
5. confidence: Confidence of classification between 0 to 1

Respond ONLY in the following JSON format:
{
  "category": "",
  "intent": "",
  "subtopics": ["", "", ""],
  "focus": "",
  "confidence": 0.9
}

Prompt: {prompt}
"""

class PromptClassifier:
    def __init__(self, api_key: str):
        openai.api_key = api_key
        self.model = "gpt-3.5-turbo"

    def classify(self, prompt: str) -> Dict:
        try:
            logger.info("Classifying user prompt...")
            system_prompt = CLASSIFICATION_PROMPT.format(prompt=prompt)

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": system_prompt},
                ],
                temperature=0.5,
                max_tokens=300
            )

            content = response['choices'][0]['message']['content']
            logger.debug(f"Raw classification response: {content}")

            # Evaluate response safely
            import json
            result = json.loads(content)

            logger.info("Classification complete")
            return result

        except Exception as e:
            logger.exception(f"Prompt classification failed: {e}")
            return {
                "category": "General",
                "intent": "Inform",
                "subtopics": [],
                "focus": prompt[:30],
                "confidence": 0.5
            }

def get_classifier(api_key: str) -> PromptClassifier:
    return PromptClassifier(api_key=api_key)
