import io

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestBorrowEndpoints:
    async def _create_book(self, client: AsyncClient) -> dict:
        response = await client.post(
            "/books",
            data={"title": "Borrowable", "author": "Author", "genre": "Fiction"},
            files={"file": ("test.pdf", io.BytesIO(b"pdf"), "application/pdf")},
        )
        return response.json()

    async def test_borrow_book(self, client: AsyncClient) -> None:
        book = await self._create_book(client)
        response = await client.post(f"/books/{book['id']}/borrow")
        assert response.status_code == 201
        data = response.json()
        assert data["is_active"] is True
        assert data["book_id"] == book["id"]

    async def test_return_book(self, client: AsyncClient) -> None:
        book = await self._create_book(client)
        await client.post(f"/books/{book['id']}/borrow")

        response = await client.post(f"/books/{book['id']}/return")
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False
        assert data["returned_at"] is not None

    async def test_double_borrow_returns_409(self, client: AsyncClient) -> None:
        book = await self._create_book(client)
        await client.post(f"/books/{book['id']}/borrow")

        response = await client.post(f"/books/{book['id']}/borrow")
        assert response.status_code == 409

    async def test_return_without_borrow_returns_404(self, client: AsyncClient) -> None:
        book = await self._create_book(client)
        response = await client.post(f"/books/{book['id']}/return")
        assert response.status_code == 404
