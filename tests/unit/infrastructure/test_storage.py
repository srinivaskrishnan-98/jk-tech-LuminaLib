import io

import pytest

from tests.conftest import InMemoryStorage


@pytest.mark.asyncio
class TestInMemoryStorage:
    async def test_upload_and_download(self) -> None:
        storage = InMemoryStorage()
        content = io.BytesIO(b"file content here")
        key = await storage.upload_file(content, "test/file.pdf", "application/pdf")
        assert key == "test/file.pdf"

        downloaded = await storage.download_file("test/file.pdf")
        assert downloaded == b"file content here"

    async def test_file_exists(self) -> None:
        storage = InMemoryStorage()
        assert await storage.file_exists("nonexistent") is False

        content = io.BytesIO(b"data")
        await storage.upload_file(content, "exists.txt", "text/plain")
        assert await storage.file_exists("exists.txt") is True

    async def test_delete_file(self) -> None:
        storage = InMemoryStorage()
        content = io.BytesIO(b"data")
        await storage.upload_file(content, "delete_me.txt", "text/plain")
        assert await storage.file_exists("delete_me.txt") is True

        await storage.delete_file("delete_me.txt")
        assert await storage.file_exists("delete_me.txt") is False

    async def test_download_nonexistent_raises(self) -> None:
        storage = InMemoryStorage()
        with pytest.raises(FileNotFoundError):
            await storage.download_file("nonexistent")
