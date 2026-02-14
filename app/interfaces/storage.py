from abc import ABC, abstractmethod
from typing import BinaryIO


class StorageBackend(ABC):
    """Abstract interface for file storage operations.

    Implementations: MinIOStorage, LocalStorage.
    Swap via STORAGE_BACKEND env variable.
    """

    @abstractmethod
    async def upload_file(
        self,
        file_content: BinaryIO,
        file_key: str,
        content_type: str,
    ) -> str:
        """Upload a file and return the storage key/path."""
        ...

    @abstractmethod
    async def download_file(self, file_key: str) -> bytes:
        """Download a file by its storage key. Returns raw bytes."""
        ...

    @abstractmethod
    async def delete_file(self, file_key: str) -> None:
        """Delete a file by its storage key."""
        ...

    @abstractmethod
    async def file_exists(self, file_key: str) -> bool:
        """Check if a file exists in storage."""
        ...
