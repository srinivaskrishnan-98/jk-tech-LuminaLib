from app.config import Settings
from app.interfaces.storage import StorageBackend


def create_storage_backend(settings: Settings) -> StorageBackend:
    """Factory function that returns the configured storage backend.

    Controlled by STORAGE_BACKEND env variable: "minio" or "local".
    """
    match settings.STORAGE_BACKEND:
        case "minio":
            from app.infrastructure.storage.minio_storage import MinIOStorage

            return MinIOStorage(settings)
        case "local":
            from app.infrastructure.storage.local_storage import LocalStorage

            return LocalStorage(settings)
        case _:
            raise ValueError(
                f"Unknown storage backend: {settings.STORAGE_BACKEND}. "
                "Supported: 'minio', 'local'"
            )
