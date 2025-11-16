"""Chat API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.message import ChatRequest, ChatResponse
from app.services.assistant_service import (
    AssistantService,
    ConversationNotFoundError,
    DatabaseError,
    AgentError,
    AssistantServiceError
)
from app.services.conversation_service import ConversationService
from app.utils.auth import get_current_active_user

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

# Initialize assistant service
assistant_service = AssistantService()


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Chat with the AI assistant.

    The assistant can help design jewelry, answer questions, and generate images.
    It will automatically call tools when appropriate.

    **Auto-conversation creation**: If no conversation_id is provided or if the conversation
    doesn't exist, a new conversation will be created automatically with a title based on
    your first message.

    Requires authentication.

    Args:
        request: Chat request with optional conversation_id, message, images and artifact
        current_user: Current authenticated user
        db: Database session

    Returns:
        ChatResponse with user and assistant messages

    Raises:
        HTTPException: 403 if conversation doesn't belong to user, 500 for errors
    """
    try:
        conversation = None

        # Check if conversation_id is provided
        if request.conversation_id:
            # Try to get existing conversation
            conversation = ConversationService.get_conversation(db, request.conversation_id)

            # If conversation exists, verify ownership
            if conversation and conversation.user_id != current_user.id:
                raise HTTPException(
                    status_code=403,
                    detail="You don't have permission to access this conversation"
                )

        # Auto-create conversation if not provided or not found
        if not conversation:
            # Generate title from first message (first 50 chars)
            title = request.message[:50]
            if len(request.message) > 50:
                title += "..."

            # Create new conversation
            from app.schemas.conversation import ConversationCreate
            conversation = ConversationService.create_conversation(
                db=db,
                user_id=current_user.id,
                conversation_data=ConversationCreate(title=title)
            )

            # Update request with new conversation_id
            request.conversation_id = conversation.id

        # Process chat through assistant service
        response = await assistant_service.chat(
            db=db,
            chat_request=request,
            user_id=current_user.id
        )
        return response

    except HTTPException:
        raise

    except ConversationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except AgentError as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI agent error: {str(e)}"
        )

    except DatabaseError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )

    except AssistantServiceError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Service error: {str(e)}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )
