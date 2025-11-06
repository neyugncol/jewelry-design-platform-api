"""Image API endpoints for upload and retrieval."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.models.user import User
from app.services.image_service import ImageService
from app.services.conversation_service import ConversationService
from app.schemas.image import ImageResponse, ImageListResponse
from app.utils.auth import get_current_active_user

router = APIRouter(prefix="/api/v1/images", tags=["images"])
image_service = ImageService()


@router.post("/upload", response_model=ImageResponse, status_code=201)
async def upload_image(
    file: UploadFile = File(...),
    conversation_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload an image file and store as base64.

    Requires authentication. If conversation_id is provided, it must belong to the authenticated user.

    Args:
        file: Image file to upload
        conversation_id: Optional conversation ID to associate with
        current_user: Current authenticated user
        db: Database session

    Returns:
        ImageResponse with image details and base64 data
    """
    # If conversation_id provided, verify it belongs to user
    if conversation_id:
        conversation = ConversationService.get_conversation(db, conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if conversation.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="You don't have permission to access this conversation")

    # Read file content
    file_content = await file.read()

    # Validate file
    is_valid, error_message = image_service.validate_image_file(
        file.content_type,
        len(file_content)
    )

    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)

    # Save image
    image = image_service.save_image(
        file_content=file_content,
        filename=file.filename,
        content_type=file.content_type,
        user_id=current_user.id,
        db=db,
        conversation_id=conversation_id
    )

    return ImageResponse(
        id=image.id,
        user_id=image.user_id,
        filename=image.filename,
        content_type=image.content_type,
        image_data=image.image_data,
        conversation_id=image.conversation_id,
        created_at=image.created_at
    )


@router.get("/{image_id}", response_model=ImageResponse)
async def get_image(
    image_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get an image by ID.

    Requires authentication. The image must belong to the authenticated user.

    Args:
        image_id: Image ID (UUID string)
        current_user: Current authenticated user
        db: Database session

    Returns:
        ImageResponse with image details and base64 data
    """
    image = image_service.get_image_by_id(db, image_id)

    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    # Verify image belongs to user
    if image.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You don't have permission to access this image")

    return ImageResponse(
        id=image.id,
        user_id=image.user_id,
        filename=image.filename,
        content_type=image.content_type,
        image_data=image.image_data,
        conversation_id=image.conversation_id,
        created_at=image.created_at
    )


@router.get("/", response_model=ImageListResponse)
async def list_images(
    page: int = 1,
    page_size: int = 20,
    conversation_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List images with pagination.

    Requires authentication. Only returns images belonging to the authenticated user.

    Args:
        page: Page number (starts at 1)
        page_size: Number of images per page
        conversation_id: Optional filter by conversation ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        ImageListResponse with paginated image list
    """
    # Calculate skip
    skip = (page - 1) * page_size

    # Get images for user
    if conversation_id:
        # Verify conversation belongs to user
        conversation = ConversationService.get_conversation(db, conversation_id)
        if conversation and conversation.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="You don't have permission to access this conversation")

        images = image_service.get_images_by_conversation(
            db, conversation_id, skip, page_size
        )
        from app.models.image import Image
        total = db.query(Image).filter(
            Image.conversation_id == conversation_id,
            Image.user_id == current_user.id
        ).count()
    else:
        images, total = image_service.get_images_by_user(db, current_user.id, skip, page_size)

    # Build responses
    image_responses = [
        ImageResponse(
            id=img.id,
            user_id=img.user_id,
            filename=img.filename,
            content_type=img.content_type,
            image_data=img.image_data,
            conversation_id=img.conversation_id,
            created_at=img.created_at
        )
        for img in images
    ]

    return ImageListResponse(
        images=image_responses,
        total=total,
        page=page,
        page_size=page_size
    )


@router.delete("/{image_id}", status_code=204)
async def delete_image(
    image_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete an image.

    Requires authentication. The image must belong to the authenticated user.

    Args:
        image_id: Image ID (UUID string)
        current_user: Current authenticated user
        db: Database session

    Returns:
        204 No Content on success
    """
    # Get image and verify ownership
    image = image_service.get_image_by_id(db, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    if image.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You don't have permission to delete this image")

    success = image_service.delete_image(db, image_id)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete image")

    return None


@router.get("/conversation/{conversation_id}", response_model=ImageListResponse)
async def get_conversation_images(
    conversation_id: str,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all images for a specific conversation.

    Requires authentication. The conversation must belong to the authenticated user.

    Args:
        conversation_id: Conversation ID
        page: Page number (starts at 1)
        page_size: Number of images per page
        current_user: Current authenticated user
        db: Database session

    Returns:
        ImageListResponse with images for the conversation
    """
    # Verify conversation belongs to user
    conversation = ConversationService.get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if conversation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You don't have permission to access this conversation")

    # Calculate skip
    skip = (page - 1) * page_size

    # Get images
    images = image_service.get_images_by_conversation(
        db, conversation_id, skip, page_size
    )

    # Get total count
    from app.models.image import Image
    total = db.query(Image).filter(
        Image.conversation_id == conversation_id,
        Image.user_id == current_user.id
    ).count()

    # Build responses
    image_responses = [
        ImageResponse(
            id=img.id,
            user_id=img.user_id,
            filename=img.filename,
            content_type=img.content_type,
            image_data=img.image_data,
            conversation_id=img.conversation_id,
            created_at=img.created_at
        )
        for img in images
    ]

    return ImageListResponse(
        images=image_responses,
        total=total,
        page=page,
        page_size=page_size
    )
