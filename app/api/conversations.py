"""Conversation API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationListResponse,
    ConversationDetailResponse,
)
from app.services.conversation_service import ConversationService
from app.utils.auth import get_current_active_user

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])


@router.post("", response_model=ConversationResponse, status_code=201)
def create_conversation(
    conversation: ConversationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new conversation.

    This endpoint creates a new conversation session for chatting with the AI.
    The conversation will belong to the authenticated user.

    Requires authentication.
    """
    created = ConversationService.create_conversation(
        db=db,
        conversation_data=conversation,
        user_id=current_user.id
    )
    return created


@router.get("", response_model=ConversationListResponse)
def list_conversations(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all conversations.

    Returns a paginated list of conversations for the authenticated user.

    Requires authentication.
    """
    conversations, total = ConversationService.list_conversations(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset
    )

    return ConversationListResponse(
        conversations=conversations,
        total=total
    )


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a conversation by ID.

    Returns detailed information about a conversation including all messages.
    The conversation must belong to the authenticated user.

    Requires authentication.
    """
    conversation = ConversationService.get_conversation_with_messages(
        db=db,
        conversation_id=conversation_id
    )

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Verify conversation belongs to user
    if conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to access this conversation"
        )

    return conversation


@router.delete("/{conversation_id}", status_code=204)
def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a conversation.

    Deletes a conversation and all its messages.
    The conversation must belong to the authenticated user.

    Requires authentication.
    """
    conversation = ConversationService.get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Verify conversation belongs to user
    if conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to delete this conversation"
        )

    success = ConversationService.delete_conversation(db, conversation_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete conversation")

    return None
