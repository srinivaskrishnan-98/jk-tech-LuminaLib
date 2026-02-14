from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract interface for LLM operations.

    Implementations: OllamaProvider, MockProvider.
    Swap via LLM_PROVIDER env variable.
    """

    @abstractmethod
    async def generate_summary(self, text: str, max_length: int = 500) -> str:
        """Generate a summary of the provided text."""
        ...

    @abstractmethod
    async def analyze_sentiment(self, text: str) -> dict:
        """Analyze sentiment of text. Returns {"score": float, "label": str}."""
        ...

    @abstractmethod
    async def generate_review_consensus(self, reviews: list[str]) -> str:
        """Generate a rolling consensus summary from multiple review texts."""
        ...
