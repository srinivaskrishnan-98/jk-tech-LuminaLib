import io

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestReviewEndpoints:
    async def _create_and_borrow_book(self, client: AsyncClient) -> dict:
        book_resp = await client.post(
            "/books",
            data={"title": "Review Book", "author": "Author", "genre": "Fiction"},
            files={"file": ("test.pdf", io.BytesIO(b"pdf"), "application/pdf")},
        )
        book = book_resp.json()
        await client.post(f"/books/{book['id']}/borrow")
        return book

    async def test_submit_review_after_borrowing(self, client: AsyncClient) -> None:
        book = await self._create_and_borrow_book(client)
        response = await client.post(
            f"/books/{book['id']}/reviews",
            json={"rating": 5, "review_text": "This is an excellent book that I really enjoyed!"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["rating"] == 5
        assert data["book_id"] == book["id"]

    async def test_review_without_borrowing_returns_403(self, client: AsyncClient) -> None:
        book_resp = await client.post(
            "/books",
            data={"title": "No Borrow Book", "author": "Author", "genre": "Science"},
            files={"file": ("test.pdf", io.BytesIO(b"pdf"), "application/pdf")},
        )
        book = book_resp.json()

        response = await client.post(
            f"/books/{book['id']}/reviews",
            json={"rating": 3, "review_text": "Trying to review without borrowing this book."},
        )
        assert response.status_code == 403

    async def test_get_book_analysis(self, client: AsyncClient) -> None:
        book = await self._create_and_borrow_book(client)

        response = await client.get(f"/books/{book['id']}/analysis")
        assert response.status_code == 200
        data = response.json()
        assert data["book_id"] == book["id"]
        assert "total_reviews" in data
        assert "rating_distribution" in data
