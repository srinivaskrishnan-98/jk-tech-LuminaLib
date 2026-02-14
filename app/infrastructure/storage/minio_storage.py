from typing import BinaryIO

import aioboto3
import structlog
from botocore.exceptions import ClientError

from app.config import Settings
from app.interfaces.storage import StorageBackend

logger = structlog.get_logger()


class MinIOStorage(StorageBackend):
    """File storage implementation using MinIO (S3-compatible)."""

    def __init__(self, settings: Settings) -> None:
        self.endpoint_url = f"{'https' if settings.MINIO_USE_SSL else 'http'}://{settings.MINIO_ENDPOINT}"
        self.access_key = settings.MINIO_ACCESS_KEY
        self.secret_key = settings.MINIO_SECRET_KEY
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self._session = aioboto3.Session()

    def _get_client_kwargs(self) -> dict:
        return {
            "service_name": "s3",
            "endpoint_url": self.endpoint_url,
            "aws_access_key_id": self.access_key,
            "aws_secret_access_key": self.secret_key,
        }

    async def ensure_bucket_exists(self) -> None:
        """Create the storage bucket if it does not exist."""
        async with self._session.client(**self._get_client_kwargs()) as client:
            try:
                await client.head_bucket(Bucket=self.bucket_name)
            except ClientError:
                await client.create_bucket(Bucket=self.bucket_name)
                logger.info("minio_bucket_created", bucket=self.bucket_name)

    async def upload_file(
        self,
        file_content: BinaryIO,
        file_key: str,
        content_type: str,
    ) -> str:
        content = file_content.read()
        async with self._session.client(**self._get_client_kwargs()) as client:
            await client.put_object(
                Bucket=self.bucket_name,
                Key=file_key,
                Body=content,
                ContentType=content_type,
            )
        logger.info("file_uploaded_minio", file_key=file_key, size=len(content))
        return file_key

    async def download_file(self, file_key: str) -> bytes:
        async with self._session.client(**self._get_client_kwargs()) as client:
            response = await client.get_object(Bucket=self.bucket_name, Key=file_key)
            return await response["Body"].read()

    async def delete_file(self, file_key: str) -> None:
        async with self._session.client(**self._get_client_kwargs()) as client:
            await client.delete_object(Bucket=self.bucket_name, Key=file_key)
        logger.info("file_deleted_minio", file_key=file_key)

    async def file_exists(self, file_key: str) -> bool:
        async with self._session.client(**self._get_client_kwargs()) as client:
            try:
                await client.head_object(Bucket=self.bucket_name, Key=file_key)
                return True
            except ClientError:
                return False
