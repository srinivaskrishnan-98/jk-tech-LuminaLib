import io

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestBookUpload:
    async def test_upload_pdf_book(self, client: AsyncClient) -> None:
        response = await client.post(
            "/books",
            data={
                "title": "Test Book",
                "author": "Test Author",
                "genre": "Fiction",
                "description": "A test book",
            },
            files={"file": ("test.pdf", io.BytesIO(b"fake pdf"), "application/pdf")},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Book"
        assert data["file_type"] == "pdf"
        assert data["summary_status"] == "pending"

    async def test_upload_txt_book(self, client: AsyncClient) -> None:
        response = await client.post(
            "/books",
            data={
                "title": "Text Book",
                "author": "Author",
                "genre": "Science",
            },
            files={"file": ("book.txt", io.BytesIO(b"text content"), "text/plain")},
        )
        assert response.status_code == 201
        assert response.json()["file_type"] == "txt"

    async def test_upload_rejects_unsupported_type(self, client: AsyncClient) -> None:
        response = await client.post(
            "/books",
            data={"title": "Bad", "author": "Author", "genre": "Fiction"},
            files={"file": ("bad.exe", io.BytesIO(b"data"), "application/octet-stream")},
        )
        assert response.status_code == 400


@pytest.mark.asyncio
class TestBookCRUD:
    async def _create_book(self, client: AsyncClient) -> dict:
        response = await client.post(
            "/books",
            data={"title": "CRUD Book", "author": "Author", "genre": "Fiction"},
            files={"file": ("test.pdf", io.BytesIO(b"pdf content"), "application/pdf")},
        )
        return response.json()

    async def test_list_books_paginated(self, client: AsyncClient) -> None:
        await self._create_book(client)
        response = await client.get("/books?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data

    async def test_get_book_by_id(self, client: AsyncClient) -> None:
        book = await self._create_book(client)
        response = await client.get(f"/books/{book['id']}")
        assert response.status_code == 200
        assert response.json()["id"] == book["id"]

    async def test_get_nonexistent_book_returns_404(self, client: AsyncClient) -> None:
        response = await client.get("/books/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404

    async def test_update_book(self, client: AsyncClient) -> None:
        book = await self._create_book(client)
        response = await client.put(
            f"/books/{book['id']}",
            json={"title": "Updated Title"},
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"

    async def test_delete_book(self, client: AsyncClient) -> None:
        book = await self._create_book(client)
        response = await client.delete(f"/books/{book['id']}")
        assert response.status_code == 200

        # Verify deleted
        get_response = await client.get(f"/books/{book['id']}")
        assert get_response.status_code == 404
