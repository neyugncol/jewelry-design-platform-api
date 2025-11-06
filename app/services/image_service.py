"""Image service for handling image uploads and storage."""
import base64
from typing import Optional
from sqlalchemy.orm import Session

from app.models.image import Image


class ImageService:
    """Service for handling image uploads and base64 storage."""

    def save_image(
        self,
        file_content: bytes,
        filename: str,
        content_type: str,
        user_id: str,
        db: Session,
        conversation_id: Optional[str] = None
    ) -> Image:
        """
        Save image as base64 in database.

        Args:
            file_content: Binary content of the file
            filename: Original filename
            content_type: MIME type of the file
            user_id: ID of the user who owns this image
            db: Database session
            conversation_id: Optional conversation ID to associate with

        Returns:
            Image database record
        """
        # Encode to base64
        image_base64 = base64.b64encode(file_content).decode('utf-8')

        # Create database record
        image = Image(
            user_id=user_id,
            filename=filename,
            content_type=content_type,
            image_data=image_base64,
            conversation_id=conversation_id
        )

        db.add(image)
        db.commit()
        db.refresh(image)

        return image

    def get_image_by_id(self, db: Session, image_id: str) -> Optional[Image]:
        """
        Get image by ID.

        Args:
            db: Database session
            image_id: Image ID (UUID string)

        Returns:
            Image record or None
        """
        return db.query(Image).filter(Image.id == image_id).first()

    def get_images_by_conversation(
        self,
        db: Session,
        conversation_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> list[Image]:
        """
        Get all images for a conversation.

        Args:
            db: Database session
            conversation_id: Conversation ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Image records
        """
        return (
            db.query(Image)
            .filter(Image.conversation_id == conversation_id)
            .order_by(Image.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_images_by_user(
        self,
        db: Session,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[list[Image], int]:
        """
        Get all images for a user with pagination.

        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (list of Image records, total count)
        """
        query = db.query(Image).filter(Image.user_id == user_id).order_by(Image.created_at.desc())
        total = query.count()
        images = query.offset(skip).limit(limit).all()
        return images, total

    def get_all_images(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[list[Image], int]:
        """
        Get all images with pagination.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (list of Image records, total count)
        """
        query = db.query(Image).order_by(Image.created_at.desc())
        total = query.count()
        images = query.offset(skip).limit(limit).all()
        return images, total

    def delete_image(self, db: Session, image_id: str) -> bool:
        """
        Delete an image from database.

        Args:
            db: Database session
            image_id: Image ID (UUID string)

        Returns:
            True if deleted successfully, False otherwise
        """
        image = self.get_image_by_id(db, image_id)
        if not image:
            return False

        db.delete(image)
        db.commit()

        return True

    def validate_image_file(self, content_type: str, file_size: int) -> tuple[bool, Optional[str]]:
        """
        Validate uploaded image file.

        Args:
            content_type: MIME type of the file
            file_size: Size of the file in bytes

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Allowed image types
        allowed_types = [
            "image/jpeg",
            "image/jpg",
            "image/png",
            "image/gif",
            "image/webp",
            "image/bmp"
        ]

        # Check content type
        if content_type not in allowed_types:
            return False, f"Invalid file type. Allowed types: {', '.join(allowed_types)}"

        # Check file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB in bytes
        if file_size > max_size:
            return False, f"File too large. Maximum size: {max_size / (1024 * 1024)}MB"

        return True, None
