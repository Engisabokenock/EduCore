"""Cloudflare R2 / S3 object storage."""
import logging
from typing import Optional
from urllib.parse import urlparse

from app.core.config import settings
from app.core.exceptions import ServiceUnavailableError

logger = logging.getLogger("educore.storage")


class StorageProvider:
    """Uploads objects and produces download URLs for them."""

    def __init__(self):
        self._session = None

    def _get_client(self):
        if not settings.storage_configured:
            raise ServiceUnavailableError("File storage is not configured on this server.")
        if self._session is None:
            import aioboto3  # imported lazily so the API boots without storage credentials

            self._session = aioboto3.Session()
        return self._session.client(
            "s3",
            endpoint_url=settings.CLOUDFLARE_ENDPOINT,
            aws_access_key_id=settings.CLOUDFLARE_ACCESS_KEY,
            aws_secret_access_key=settings.CLOUDFLARE_SECRET_KEY,
            region_name="auto",
        )

    async def upload_file(self, file_data: bytes, destination_key: str, content_type: str) -> str:
        """Store the object and return its canonical URL (resolved to a download URL on demand)."""
        async with self._get_client() as client:
            await client.put_object(
                Bucket=settings.BUCKET_NAME,
                Key=destination_key,
                Body=file_data,
                ContentType=content_type,
            )
        return self.canonical_url(destination_key)

    @staticmethod
    def canonical_url(key: str) -> str:
        if settings.PUBLIC_ASSET_BASE_URL:
            return f"{settings.PUBLIC_ASSET_BASE_URL.rstrip('/')}/{key}"
        return f"{(settings.CLOUDFLARE_ENDPOINT or '').rstrip('/')}/{settings.BUCKET_NAME}/{key}"

    @staticmethod
    def key_from_url(url: str) -> Optional[str]:
        """Return the object key when ``url`` points at our private bucket endpoint."""
        if not settings.CLOUDFLARE_ENDPOINT or not url:
            return None
        endpoint = urlparse(settings.CLOUDFLARE_ENDPOINT)
        parsed = urlparse(url)
        if parsed.netloc != endpoint.netloc:
            return None
        prefix = f"/{settings.BUCKET_NAME}/"
        return parsed.path[len(prefix):] if parsed.path.startswith(prefix) else None

    async def download_url(self, stored_url: str, filename: Optional[str] = None) -> str:
        """
        Turn a stored file URL into something a browser can fetch.

        Private R2 endpoint URLs are not publicly readable, so they are exchanged for a
        short-lived presigned URL. Public/CDN URLs and external links pass through.
        """
        key = self.key_from_url(stored_url)
        if key is None or not settings.storage_configured:
            return stored_url
        params = {"Bucket": settings.BUCKET_NAME, "Key": key}
        if filename:
            params["ResponseContentDisposition"] = f'attachment; filename="{filename}"'
        async with self._get_client() as client:
            return await client.generate_presigned_url(
                "get_object", Params=params, ExpiresIn=settings.PRESIGNED_URL_TTL_SECONDS
            )
