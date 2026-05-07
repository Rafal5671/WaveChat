import io
import os
import uuid

import boto3
from botocore.client import Config
from PIL import Image

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "wavechat-media")
MINIO_USE_SSL = os.getenv("MINIO_USE_SSL", "False") == "True"

ALLOWED_MIME_TYPES = {
    "image": ["image/jpeg", "image/png", "image/gif", "image/webp"],
    "video": ["video/mp4", "video/webm", "video/quicktime"],
    "audio": ["audio/mpeg", "audio/ogg", "audio/wav"],
    "file": [
        "application/pdf",
        "application/zip",
        "text/plain",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ],
}

MAX_FILE_SIZES = {
    "image": 10 * 1024 * 1024,
    "video": 200 * 1024 * 1024,
    "audio": 50 * 1024 * 1024,
    "file": 100 * 1024 * 1024,
}


def get_s3_client():
    """Create and return a boto3 S3 client pointed at MinIO."""
    return boto3.client(
        "s3",
        endpoint_url=f"{'https' if MINIO_USE_SSL else 'http'}://{MINIO_ENDPOINT}",
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def ensure_bucket_exists(s3_client):
    """Create the media bucket if it does not already exist."""
    try:
        s3_client.head_bucket(Bucket=MINIO_BUCKET)
    except Exception:
        s3_client.create_bucket(Bucket=MINIO_BUCKET)


def upload_file(
    file_bytes: bytes,
    mime_type: str,
    media_type: str,
    user_id: str,
    file_name: str,
) -> dict:
    """
    Upload a file to MinIO and return URL and metadata.

    Generates a thumbnail for image uploads.
    Returns a dict with url, thumbnail_url, object_key and file_id.
    """
    s3 = get_s3_client()
    ensure_bucket_exists(s3)

    file_id = str(uuid.uuid4())
    ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else "bin"
    object_key = f"{media_type}s/{user_id}/{file_id}.{ext}"

    s3.put_object(
        Bucket=MINIO_BUCKET,
        Key=object_key,
        Body=file_bytes,
        ContentType=mime_type,
    )

    url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": MINIO_BUCKET, "Key": object_key},
        ExpiresIn=365 * 24 * 3600,
    )

    thumbnail_url = None
    if media_type == "image":
        thumbnail_url = _generate_thumbnail(s3, file_bytes, user_id, file_id)

    return {
        "file_id": file_id,
        "url": url,
        "thumbnail_url": thumbnail_url,
        "object_key": object_key,
    }


def _generate_thumbnail(
    s3,
    file_bytes: bytes,
    user_id: str,
    file_id: str,
    size: tuple = (320, 320),
) -> str | None:
    """
    Generate a resized thumbnail and upload it to MinIO.

    Returns the presigned URL of the thumbnail or None on failure.
    """
    try:
        img = Image.open(io.BytesIO(file_bytes))
        img.thumbnail(size, Image.LANCZOS)

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85, optimize=True)
        buffer.seek(0)

        thumb_key = f"thumbnails/{user_id}/{file_id}_thumb.jpg"
        s3.put_object(
            Bucket=MINIO_BUCKET,
            Key=thumb_key,
            Body=buffer.getvalue(),
            ContentType="image/jpeg",
        )

        return s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": MINIO_BUCKET, "Key": thumb_key},
            ExpiresIn=365 * 24 * 3600,
        )
    except Exception:
        return None
