import mimetypes
import os

from auth import SimpleUser, get_current_user
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from schemas import ErrorResponse, UploadResponse
from storage import ALLOWED_MIME_TYPES, MAX_FILE_SIZES, upload_file

load_dotenv()

app = FastAPI(
    title="WaveChat Media Service",
    description="Handles file uploads and storage for WaveChat.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "media_service"}


@app.post(
    "/api/media/upload/",
    response_model=UploadResponse,
    responses={
        401: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        415: {"model": ErrorResponse},
    },
)
async def upload(
    file: UploadFile = File(...),
    media_type: str = Form(default="file"),
    current_user: SimpleUser = Depends(get_current_user),
):
    """
    Upload a file to MinIO storage.

    Accepts multipart/form-data with a file and optional media_type field.
    Supported media_type values: image, video, audio, file.
    Returns a presigned URL valid for one year.
    """
    mime_type, _ = mimetypes.guess_type(file.filename or "")

    if not mime_type:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Could not determine file type.",
        )

    allowed = ALLOWED_MIME_TYPES.get(media_type, [])
    if mime_type not in allowed:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '{mime_type}' not allowed for media type '{media_type}'.",
        )

    file_bytes = await file.read()
    max_size = MAX_FILE_SIZES.get(media_type, 10 * 1024 * 1024)

    if len(file_bytes) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max size: {max_size // 1024 // 1024}MB.",
        )

    result = upload_file(
        file_bytes=file_bytes,
        mime_type=mime_type,
        media_type=media_type,
        user_id=current_user.id,
        file_name=file.filename or "upload",
    )

    return UploadResponse(
        id=result["file_id"],
        url=result["url"],
        thumbnail_url=result["thumbnail_url"],
        media_type=media_type,
        mime_type=mime_type,
        size_bytes=len(file_bytes),
        file_name=file.filename or "upload",
    )
