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

    Requires authentication. The conversation must belong to the authenticated user.

    Args:
        request: Chat request with conversation_id, message, optional images and artifact
        current_user: Current authenticated user
        db: Database session

    Returns:
        ChatResponse with user and assistant messages

    Raises:
        HTTPException: 403 if conversation doesn't belong to user, 404 if not found, 500 for errors
    """
    try:
        # Verify conversation belongs to user
        conversation = ConversationService.get_conversation(db, request.conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        if conversation.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to access this conversation"
            )

        # Process chat through assistant service
        response = await assistant_service.chat(
            db=db,
            chat_request=request
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
