from pydantic import BaseModel


class UploadResponse(BaseModel):
    """Response returned after a successful file upload."""

    id: str
    url: str
    thumbnail_url: str | None
    media_type: str
    mime_type: str
    size_bytes: int
    file_name: str


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
