from app.config import Settings
from app.interfaces.llm import LLMProvider


def create_llm_provider(settings: Settings) -> LLMProvider:
    """Factory function that returns the configured LLM provider.

    Controlled by LLM_PROVIDER env variable: "ollama", "openai", or "mock".
    """
    match settings.LLM_PROVIDER:
        case "ollama":
            from app.infrastructure.llm.ollama_provider import OllamaProvider

            return OllamaProvider(settings)
        case "mock":
            from app.infrastructure.llm.mock_provider import MockLLMProvider

            return MockLLMProvider()
        case _:
            raise ValueError(
                f"Unknown LLM provider: {settings.LLM_PROVIDER}. "
                "Supported: 'ollama', 'mock'"
            )
