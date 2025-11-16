"""File API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File as FastAPIFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from app.db.database import get_db
from app.schemas.file import FileUploadResponse, FileResponse, FileListResponse
from app.services.file_service import (
    FileService,
    FileNotFoundError,
    FileServiceError
)
from app.utils.auth import get_current_active_user
from app.models.user import User


router = APIRouter(prefix="/api/v1/files", tags=["files"])


@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload a file and get a short ID for easy LLM reference.

    The file will be saved to the data volume and a short, easy-to-reference ID
    will be generated (e.g., 'a3f9k2m7'). This ID can be used in LLM conversations
    to reference the file.

    Args:
        file: The file to upload
        current_user: Current authenticated user
        db: Database session

    Returns:
        FileUploadResponse with short_id and metadata

    Raises:
        HTTPException: 400 if file is empty, 500 for other errors
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required"
            )

        # Get content type
        content_type = file.content_type or "application/octet-stream"

        # Save file
        file_record = FileService.save_file(
            db=db,
            file_content=file.file,
            filename=file.filename,
            content_type=content_type,
            user_id=current_user.id
        )

        return FileUploadResponse(
            short_id=file_record.short_id,
            filename=file_record.filename,
            content_type=file_record.content_type,
            file_size=file_record.file_size,
            created_at=file_record.created_at
        )

    except FileServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{short_id}/download")
async def download_file(
    short_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Download a file by its short ID.

    Retrieves the file content from the data volume and streams it back.

    Args:
        short_id: The short ID of the file (e.g., 'a3f9k2m7')
        current_user: Current authenticated user
        db: Database session

    Returns:
        StreamingResponse with file content

    Raises:
        HTTPException: 404 if file not found, 500 for other errors
    """
    try:
        file_record, content = FileService.load_file(db, short_id)

        # Create streaming response
        return StreamingResponse(
            io.BytesIO(content),
            media_type=file_record.content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{file_record.filename}"'
            }
        )

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except FileServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{short_id}", response_model=FileResponse)
async def get_file_metadata(
    short_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get file metadata by short ID.

    Returns metadata about the file without downloading the content.

    Args:
        short_id: The short ID of the file
        current_user: Current authenticated user
        db: Database session

    Returns:
        FileResponse with file metadata

    Raises:
        HTTPException: 404 if file not found
    """
    file_record = FileService.get_file_by_short_id(db, short_id)
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with short_id '{short_id}' not found"
        )

    return file_record


@router.delete("/{short_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    short_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a file by its short ID.

    Removes the file from both the database and the data volume.
    Users can only delete their own files.

    Args:
        short_id: The short ID of the file
        current_user: Current authenticated user
        db: Database session

    Raises:
        HTTPException: 404 if file not found, 403 if unauthorized
    """
    try:
        # Check if file exists and belongs to user
        file_record = FileService.get_file_by_short_id(db, short_id)
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File with short_id '{short_id}' not found"
            )

        # Check ownership
        if file_record.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this file"
            )

        FileService.delete_file(db, short_id)
        return None

    except HTTPException:
        raise
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except FileServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("", response_model=FileListResponse)
async def list_files(
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List files for the current user.

    Returns a paginated list of files uploaded by the current user.

    Args:
        limit: Maximum number of files to return (default: 100)
        offset: Number of files to skip (default: 0)
        current_user: Current authenticated user
        db: Database session

    Returns:
        FileListResponse with list of files and total count
    """
    try:
        files, total = FileService.list_files(
            db=db,
            user_id=current_user.id,
            limit=limit,
            offset=offset
        )

        return FileListResponse(
            files=files,
            total=total
        )

    except FileServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
