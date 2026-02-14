import httpx
import structlog

from app.config import Settings
from app.interfaces.llm import LLMProvider

logger = structlog.get_logger()

# Structured, reusable prompt templates
SUMMARIZE_PROMPT = """You are a professional book summarizer. Provide a concise,
informative summary
of the following book content. Focus on the main themes, key arguments, and important takeaways.
Keep the summary under {max_length} words.

Book content:
{text}

Summary:"""

SENTIMENT_PROMPT = """Analyze the sentiment of the following book review. Respond with ONLY a JSON
object containing "score" (float 0.0 to 1.0, where 1.0 is most positive) and "label" (one of:
"positive", "negative", "neutral").

Review:
{text}

JSON Response:"""

CONSENSUS_PROMPT = """You are analyzing multiple book reviews to create a reader consensus summary.
Synthesize the following reviews into a cohesive summary of reader sentiment. Include:
- Overall reader impression
- Common praise points
- Common criticisms
- Who would enjoy this book

Reviews:
{reviews}

Consensus Summary:"""


class OllamaProvider(LLMProvider):
    """LLM provider using Ollama's OpenAI-compatible API."""

    def __init__(self, settings: Settings) -> None:
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL

    async def _call_llm(self, prompt: str) -> str:
        """Send a prompt to Ollama and return the response text."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                },
            )
            response.raise_for_status()
            return response.json()["response"]

    async def generate_summary(self, text: str, max_length: int = 500) -> str:
        logger.info("ollama_summarizing", model=self.model, text_length=len(text))
        # Truncate very long texts to avoid context window issues
        truncated = text[:10000] if len(text) > 10000 else text
        prompt = SUMMARIZE_PROMPT.format(text=truncated, max_length=max_length)
        return await self._call_llm(prompt)

    async def analyze_sentiment(self, text: str) -> dict:
        logger.info("ollama_analyzing_sentiment", model=self.model)
        prompt = SENTIMENT_PROMPT.format(text=text)
        response = await self._call_llm(prompt)

        # Parse JSON from response
        import json

        try:
            # Try to extract JSON from the response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(response[start:end])
        except (json.JSONDecodeError, ValueError):
            logger.warning("ollama_sentiment_parse_failed", response=response[:100])

        return {"score": 0.5, "label": "neutral"}

    async def generate_review_consensus(self, reviews: list[str]) -> str:
        logger.info("ollama_generating_consensus", model=self.model, review_count=len(reviews))
        reviews_text = "\n---\n".join(reviews)
        prompt = CONSENSUS_PROMPT.format(reviews=reviews_text)
        return await self._call_llm(prompt)
