import os
from pathlib import Path
from typing import BinaryIO

import aiofiles
import structlog

from app.config import Settings
from app.interfaces.storage import StorageBackend

logger = structlog.get_logger()


class LocalStorage(StorageBackend):
    """File storage implementation using the local filesystem."""

    def __init__(self, settings: Settings) -> None:
        self.base_path = Path(settings.LOCAL_STORAGE_PATH)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def upload_file(
        self,
        file_content: BinaryIO,
        file_key: str,
        content_type: str,
    ) -> str:
        file_path = self.base_path / file_key
        file_path.parent.mkdir(parents=True, exist_ok=True)

        content = file_content.read()
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

        logger.info("file_uploaded_locally", file_key=file_key, size=len(content))
        return file_key

    async def download_file(self, file_key: str) -> bytes:
        file_path = self.base_path / file_key
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_key}")

        async with aiofiles.open(file_path, "rb") as f:
            return await f.read()

    async def delete_file(self, file_key: str) -> None:
        file_path = self.base_path / file_key
        if file_path.exists():
            os.remove(file_path)
            logger.info("file_deleted_locally", file_key=file_key)

    async def file_exists(self, file_key: str) -> bool:
        return (self.base_path / file_key).exists()
