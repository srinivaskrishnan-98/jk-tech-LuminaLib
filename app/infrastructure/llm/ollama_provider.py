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
        """Send a prompt to Ollama and return the response text using streaming to avoid timeouts."""
        # Use streaming mode to avoid Ollama's 2-minute server timeout
        timeout = httpx.Timeout(600.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                full_response = ""
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": True,  # Enable streaming to avoid timeout
                        "options": {
                            "num_predict": 800,  # Reduced from 1000 for faster generation
                            "temperature": 0.5,  # Lower temp = more focused, faster
                            "num_ctx": 4096,  # Context window
                            "num_batch": 512,  # Process more tokens at once
                            "num_gpu": 1,  # Use GPU if available
                        },
                    },
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line:
                            import json
                            try:
                                chunk = json.loads(line)
                                if "response" in chunk:
                                    full_response += chunk["response"]
                                if chunk.get("done", False):
                                    break
                            except json.JSONDecodeError:
                                continue
                return full_response
            except httpx.TimeoutException as e:
                logger.error(
                    "ollama_timeout",
                    model=self.model,
                    base_url=self.base_url,
                    prompt_length=len(prompt),
                )
                raise

    async def generate_summary(self, text: str, max_length: int = 500) -> str:
        logger.info("ollama_summarizing", model=self.model, text_length=len(text))

        # Smart sampling strategy for large books
        if len(text) > 10000:
            # For large books: sample beginning (40%), middle (30%), end (30%)
            chunk_size = 3000
            start = text[:int(chunk_size * 1.33)]  # ~4000 chars from start

            mid_point = len(text) // 2
            mid_start = max(0, mid_point - chunk_size // 2)
            middle = text[mid_start:mid_start + chunk_size]

            end_start = max(0, len(text) - chunk_size)
            end = text[end_start:]

            sampled_text = f"{start}\n\n[...middle section...]\n\n{middle}\n\n[...final section...]\n\n{end}"
            logger.info("ollama_using_smart_sampling", original_length=len(text), sampled_length=len(sampled_text))
        else:
            # For smaller books: use first 8000 chars (more context)
            sampled_text = text[:8000] if len(text) > 8000 else text

        prompt = SUMMARIZE_PROMPT.format(text=sampled_text, max_length=max_length)
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
