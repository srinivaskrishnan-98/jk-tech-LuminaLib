import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestRecommendationEndpoints:
    async def test_get_recommendations(self, client: AsyncClient) -> None:
        response = await client.get("/recommendations?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        assert "strategy" in data

    async def test_recommendations_with_default_limit(self, client: AsyncClient) -> None:
        response = await client.get("/recommendations")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["recommendations"], list)
