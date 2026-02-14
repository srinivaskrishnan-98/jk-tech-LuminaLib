import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestSignupEndpoint:
    async def test_signup_success(self, client: AsyncClient) -> None:
        response = await client.post(
            "/auth/signup",
            json={
                "email": "signup@example.com",
                "username": "signupuser",
                "password": "SecurePass123",
                "full_name": "Signup User",
                "preferred_genres": ["Fiction"],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "signup@example.com"
        assert data["username"] == "signupuser"
        assert data["preferred_genres"] == ["Fiction"]

    async def test_signup_short_password_rejected(self, client: AsyncClient) -> None:
        response = await client.post(
            "/auth/signup",
            json={
                "email": "short@example.com",
                "username": "shortpass",
                "password": "123",
            },
        )
        assert response.status_code == 422

    async def test_signup_invalid_email_rejected(self, client: AsyncClient) -> None:
        response = await client.post(
            "/auth/signup",
            json={
                "email": "not-an-email",
                "username": "bademail",
                "password": "SecurePass123",
            },
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestProfileEndpoints:
    async def test_get_profile(self, client: AsyncClient) -> None:
        response = await client.get("/auth/profile")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"

    async def test_update_profile(self, client: AsyncClient) -> None:
        response = await client.put(
            "/auth/profile",
            json={"full_name": "Updated Name", "preferred_genres": ["Science", "History"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["preferred_genres"] == ["Science", "History"]
