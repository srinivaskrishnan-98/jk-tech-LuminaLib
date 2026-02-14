import pytest

from app.infrastructure.llm.mock_provider import MockLLMProvider


@pytest.mark.asyncio
class TestMockLLMProvider:
    async def test_generate_summary_returns_string(self) -> None:
        provider = MockLLMProvider()
        result = await provider.generate_summary("This is a book about Python programming.")
        assert isinstance(result, str)
        assert len(result) > 0

    async def test_analyze_sentiment_positive(self) -> None:
        provider = MockLLMProvider()
        result = await provider.analyze_sentiment("This book is great and excellent!")
        assert "score" in result
        assert "label" in result
        assert result["label"] == "positive"
        assert result["score"] > 0.5

    async def test_analyze_sentiment_negative(self) -> None:
        provider = MockLLMProvider()
        result = await provider.analyze_sentiment("This book is terrible and awful!")
        assert result["label"] == "negative"
        assert result["score"] < 0.5

    async def test_analyze_sentiment_neutral(self) -> None:
        provider = MockLLMProvider()
        result = await provider.analyze_sentiment("This book exists.")
        assert result["label"] == "neutral"
        assert result["score"] == 0.5

    async def test_generate_review_consensus(self) -> None:
        provider = MockLLMProvider()
        reviews = [
            "Rating: 5/5 - Great book, excellent writing!",
            "Rating: 4/5 - Good read, wonderful content!",
        ]
        result = await provider.generate_review_consensus(reviews)
        assert isinstance(result, str)
        assert "2" in result  # Should mention the number of reviews

    async def test_generate_consensus_empty_reviews(self) -> None:
        provider = MockLLMProvider()
        result = await provider.generate_review_consensus([])
        assert "No reviews" in result
