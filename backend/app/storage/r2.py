import aioboto3
from app.core.config import settings

class StorageProvider:
    """High performance safe bucket transport interactions handler."""
    def __init__(self):
        self.session = aioboto3.Session()

    def _get_client(self):
        return self.session.client(
            "s3",
            endpoint_url=settings.CLOUDFLARE_ENDPOINT,
            aws_access_key_id=settings.CLOUDFLARE_ACCESS_KEY,
            aws_secret_access_key=settings.CLOUDFLARE_SECRET_KEY,
        )

    async def upload_file(self, file_data: bytes, destination_key: str, content_type: str) -> str:
        async with self._get_client() as client:
            await client.put_object(
                Bucket=settings.BUCKET_NAME,
                Key=destination_key,
                Body=file_data,
                ContentType=content_type
            )
            return f"{settings.CLOUDFLARE_ENDPOINT}/{settings.BUCKET_NAME}/{destination_key}"
