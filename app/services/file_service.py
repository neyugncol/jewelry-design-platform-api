"""File service for managing file uploads and downloads."""
import os
import random
import string
from pathlib import Path
from typing import Optional, BinaryIO
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.file import File
from app.config import settings


# Characters for short ID generation (avoiding ambiguous characters)
# Excludes: 0, O, I, l, 1 to avoid confusion
SHORT_ID_CHARS = "23456789abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ"
SHORT_ID_LENGTH = 8


class FileServiceError(Exception):
    """Base exception for FileService errors."""
    pass


class FileNotFoundError(FileServiceError):
    """Raised when file is not found."""
    pass


class FileAlreadyExistsError(FileServiceError):
    """Raised when file with short_id already exists."""
    pass


class FileService:
    """Service for file upload, download, and management."""

    @staticmethod
    def generate_short_id() -> str:
        """
        Generate a short, LLM-friendly ID.

        Returns:
            8-character short ID (e.g., 'a3f9k2m7')
        """
        return ''.join(random.choices(SHORT_ID_CHARS, k=SHORT_ID_LENGTH))

    @staticmethod
    def get_upload_directory() -> Path:
        """
        Get the upload directory path from settings.

        Returns:
            Path to the upload directory
        """
        upload_dir = Path(settings.upload_directory)
        upload_dir.mkdir(parents=True, exist_ok=True)
        return upload_dir

    @staticmethod
    def save_file(
        db: Session,
        file_content: BinaryIO,
        filename: str,
        content_type: str,
        user_id: Optional[str] = None,
        max_retries: int = 5
    ) -> File:
        """
        Save a file to the data volume and create database record.

        Args:
            db: Database session
            file_content: File content as binary stream
            filename: Original filename
            content_type: MIME type of the file
            user_id: Optional user ID who uploaded the file
            max_retries: Maximum retries for generating unique short_id

        Returns:
            Created File object with short_id

        Raises:
            FileServiceError: If file save fails
        """
        try:
            # Generate unique short_id
            short_id = None
            for _ in range(max_retries):
                candidate_id = FileService.generate_short_id()
                existing = db.query(File).filter(File.short_id == candidate_id).first()
                if not existing:
                    short_id = candidate_id
                    break

            if short_id is None:
                raise FileServiceError("Failed to generate unique short_id after retries")

            # Read file content and get size
            file_content.seek(0)
            content = file_content.read()
            file_size = len(content)

            # Create subdirectory based on first 2 chars of short_id for better organization
            # e.g., short_id 'a3f9k2m7' -> 'a3/a3f9k2m7'
            upload_dir = FileService.get_upload_directory()
            subdir = upload_dir / short_id[:2]
            subdir.mkdir(parents=True, exist_ok=True)

            # Get file extension from original filename
            file_ext = Path(filename).suffix
            stored_filename = f"{short_id}{file_ext}"
            file_path = subdir / stored_filename

            # Save file to disk
            with open(file_path, 'wb') as f:
                f.write(content)

            # Create database record
            # Store relative path from upload directory
            relative_path = str(file_path.relative_to(upload_dir))

            file_record = File(
                short_id=short_id,
                filename=filename,
                file_path=relative_path,
                content_type=content_type,
                file_size=file_size,
                user_id=user_id
            )

            db.add(file_record)
            db.commit()
            db.refresh(file_record)

            return file_record

        except FileServiceError:
            raise
        except SQLAlchemyError as e:
            db.rollback()
            # Clean up file if database insert fails
            if 'file_path' in locals() and file_path.exists():
                file_path.unlink()
            raise FileServiceError(f"Failed to save file: {str(e)}") from e
        except Exception as e:
            db.rollback()
            # Clean up file if any error occurs
            if 'file_path' in locals() and file_path.exists():
                file_path.unlink()
            raise FileServiceError(f"Failed to save file: {str(e)}") from e

    @staticmethod
    def get_file_by_short_id(db: Session, short_id: str) -> Optional[File]:
        """
        Get file metadata by short_id.

        Args:
            db: Database session
            short_id: Short ID of the file

        Returns:
            File object or None if not found
        """
        return db.query(File).filter(File.short_id == short_id).first()

    @staticmethod
    def get_file_path(file_record: File) -> Path:
        """
        Get the full file path on disk.

        Args:
            file_record: File database record

        Returns:
            Full path to the file on disk
        """
        upload_dir = FileService.get_upload_directory()
        return upload_dir / file_record.file_path

    @staticmethod
    def load_file(db: Session, short_id: str) -> tuple[File, bytes]:
        """
        Load a file from the data volume.

        Args:
            db: Database session
            short_id: Short ID of the file

        Returns:
            Tuple of (File metadata, file content as bytes)

        Raises:
            FileNotFoundError: If file not found in database or on disk
        """
        try:
            # Get file metadata from database
            file_record = FileService.get_file_by_short_id(db, short_id)
            if not file_record:
                raise FileNotFoundError(f"File with short_id '{short_id}' not found")

            # Get file path
            file_path = FileService.get_file_path(file_record)

            if not file_path.exists():
                raise FileNotFoundError(f"File not found on disk: {file_path}")

            # Read file content
            with open(file_path, 'rb') as f:
                content = f.read()

            return file_record, content

        except FileNotFoundError:
            raise
        except Exception as e:
            raise FileServiceError(f"Failed to load file: {str(e)}") from e

    @staticmethod
    def delete_file(db: Session, short_id: str) -> None:
        """
        Delete a file from both database and disk.

        Args:
            db: Database session
            short_id: Short ID of the file

        Raises:
            FileNotFoundError: If file not found
        """
        try:
            file_record = FileService.get_file_by_short_id(db, short_id)
            if not file_record:
                raise FileNotFoundError(f"File with short_id '{short_id}' not found")

            # Delete file from disk
            file_path = FileService.get_file_path(file_record)
            if file_path.exists():
                file_path.unlink()

            # Delete database record
            db.delete(file_record)
            db.commit()

        except FileNotFoundError:
            raise
        except SQLAlchemyError as e:
            db.rollback()
            raise FileServiceError(f"Failed to delete file: {str(e)}") from e
        except Exception as e:
            db.rollback()
            raise FileServiceError(f"Failed to delete file: {str(e)}") from e

    @staticmethod
    def list_files(
        db: Session,
        user_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[list[File], int]:
        """
        List files with optional filtering by user.

        Args:
            db: Database session
            user_id: Optional user ID to filter files
            limit: Maximum number of files to return
            offset: Number of files to skip

        Returns:
            Tuple of (list of File objects, total count)
        """
        try:
            query = db.query(File)

            if user_id:
                query = query.filter(File.user_id == user_id)

            # Get total count
            total = query.count()

            # Get paginated results
            files = query.order_by(File.created_at.desc()).limit(limit).offset(offset).all()

            return files, total

        except SQLAlchemyError as e:
            raise FileServiceError(f"Failed to list files: {str(e)}") from e
