import structlog

from app.interfaces.llm import LLMProvider

logger = structlog.get_logger()

# Structured prompt templates used by the mock provider
SUMMARY_TEMPLATE = (
    "This book covers the following topics based on its content: {snippet}. "
    "The text explores themes and ideas presented by the author, providing "
    "readers with insights into the subject matter."
)

CONSENSUS_TEMPLATE = (
    "Based on {count} reader reviews, the overall sentiment is {sentiment}. "
    "Readers have given an average impression that reflects {tone} engagement "
    "with the material. Key themes mentioned include the quality of writing "
    "and the depth of content covered."
)


class MockLLMProvider(LLMProvider):
    """Deterministic mock LLM provider for development and testing.

    Returns structured, predictable responses without requiring
    a real LLM service. Useful for running the system without GPU
    or when Ollama is not available.
    """

    async def generate_summary(self, text: str, max_length: int = 500) -> str:
        logger.info("mock_llm_summarizing", text_length=len(text))
        snippet = text[:200].strip().replace("\n", " ")
        return SUMMARY_TEMPLATE.format(snippet=snippet)

    async def analyze_sentiment(self, text: str) -> dict:
        logger.info("mock_llm_analyzing_sentiment", text_length=len(text))
        # Simple heuristic: positive words increase score
        positive_words = {"good", "great", "excellent", "amazing", "love", "wonderful", "best"}
        negative_words = {"bad", "terrible", "awful", "hate", "worst", "boring", "poor"}

        words = set(text.lower().split())
        pos_count = len(words & positive_words)
        neg_count = len(words & negative_words)
        total = pos_count + neg_count

        if total == 0:
            score = 0.5
            label = "neutral"
        else:
            score = pos_count / total
            if score > 0.6:
                label = "positive"
            elif score < 0.4:
                label = "negative"
            else:
                label = "neutral"

        return {"score": round(score, 2), "label": label}

    async def generate_review_consensus(self, reviews: list[str]) -> str:
        logger.info("mock_llm_generating_consensus", review_count=len(reviews))
        if not reviews:
            return "No reviews available yet."

        # Aggregate simple sentiment
        total_score = 0.0
        for review in reviews:
            sentiment = await self.analyze_sentiment(review)
            total_score += sentiment["score"]

        avg_score = total_score / len(reviews)
        if avg_score > 0.6:
            sentiment = "positive"
            tone = "enthusiastic"
        elif avg_score < 0.4:
            sentiment = "negative"
            tone = "critical"
        else:
            sentiment = "mixed"
            tone = "moderate"

        return CONSENSUS_TEMPLATE.format(
            count=len(reviews), sentiment=sentiment, tone=tone
        )
