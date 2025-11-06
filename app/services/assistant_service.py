"""Assistant service for managing AI chat interactions."""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.agents.assistant_agent import AssistantAgent
from app.config import settings
from app.models.conversation import Conversation
from app.models.message import Message as MessageModel
from app.schemas.message import Message, ChatRequest, ChatResponse
from app.schemas.artifact import Artifact


class AssistantServiceError(Exception):
    """Base exception for AssistantService errors."""
    pass


class ConversationNotFoundError(AssistantServiceError):
    """Raised when conversation is not found."""
    pass


class DatabaseError(AssistantServiceError):
    """Raised when database operation fails."""
    pass


class AgentError(AssistantServiceError):
    """Raised when agent execution fails."""
    pass


class AssistantService:
    """Service for interacting with Jewelry Design Assistant."""

    def __init__(self):
        """Initialize Assistant Agent."""
        self.assistant_agent = AssistantAgent(
            model=settings.chat_model,
        )

    async def chat(
        self,
        db: Session,
        chat_request: ChatRequest
    ) -> ChatResponse:
        """
        Process a chat request and return response.

        Args:
            db: Database session
            chat_request: Chat request containing conversation_id, message, images, artifact

        Returns:
            ChatResponse with user message and assistant response

        Raises:
            ConversationNotFoundError: If conversation doesn't exist
            DatabaseError: If database operations fail
            AgentError: If agent execution fails
        """
        try:
            # Verify conversation exists
            conversation = self._get_conversation(db, chat_request.conversation_id)
            if not conversation:
                raise ConversationNotFoundError(
                    f"Conversation {chat_request.conversation_id} not found"
                )

            # Create and save user message
            user_message = await self._create_user_message(
                db=db,
                conversation_id=chat_request.conversation_id,
                content=chat_request.message,
                images=chat_request.images,
                artifact=chat_request.artifact
            )

            # Get conversation history
            conversation_messages = self._get_conversation_messages(
                db, chat_request.conversation_id
            )

            # Run assistant agent
            try:
                agent_result = await self.assistant_agent.run(
                    messages=conversation_messages,
                    enable_tools=True
                )
            except Exception as e:
                raise AgentError(f"Agent execution failed: {str(e)}") from e

            # Create and save assistant message
            assistant_message = await self._create_assistant_message(
                db=db,
                conversation_id=chat_request.conversation_id,
                content=agent_result.get("content", ""),
                tool_calls=agent_result.get("tool_calls", []),
                meta={
                    "iterations": agent_result.get("iterations"),
                    "warning": agent_result.get("warning"),
                    "error": agent_result.get("error")
                }
            )

            # Update conversation timestamp
            self._update_conversation_timestamp(db, conversation)

            return ChatResponse(
                conversation_id=chat_request.conversation_id,
                user_message=self._convert_db_message_to_schema(user_message),
                assistant_message=self._convert_db_message_to_schema(assistant_message)
            )

        except ConversationNotFoundError:
            raise
        except AgentError:
            raise
        except SQLAlchemyError as e:
            db.rollback()
            raise DatabaseError(f"Database error: {str(e)}") from e
        except Exception as e:
            db.rollback()
            raise AssistantServiceError(f"Unexpected error: {str(e)}") from e

    async def _create_user_message(
        self,
        db: Session,
        conversation_id: str,
        content: str,
        images: Optional[list[str]] = None,
        artifact: Optional[Artifact] = None
    ) -> MessageModel:
        """Create and save user message to database."""
        try:
            message = MessageModel(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                role="user",
                content=content,
                images=images if images is not None else [],
                tool_calls=[],  # User messages don't have tool calls
                artifact=artifact.model_dump() if artifact else None,
                created_at=datetime.utcnow()
            )
            db.add(message)
            db.commit()
            db.refresh(message)
            return message
        except SQLAlchemyError as e:
            db.rollback()
            raise DatabaseError(f"Failed to create user message: {str(e)}") from e

    async def _create_assistant_message(
        self,
        db: Session,
        conversation_id: str,
        content: str,
        tool_calls: Optional[list] = None,
        artifact: Optional[Artifact] = None,
        meta: Optional[dict] = None
    ) -> MessageModel:
        """Create and save assistant message to database."""
        try:
            message = MessageModel(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                role="assistant",
                content=content,
                images=[],  # Assistant messages may have images from tool calls
                tool_calls=tool_calls if tool_calls is not None else [],
                artifact=artifact.model_dump() if artifact else None,
                meta=meta,
                created_at=datetime.utcnow()
            )
            db.add(message)
            db.commit()
            db.refresh(message)
            return message
        except SQLAlchemyError as e:
            db.rollback()
            raise DatabaseError(f"Failed to create assistant message: {str(e)}") from e

    def _get_conversation(self, db: Session, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID."""
        try:
            return db.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get conversation: {str(e)}") from e

    def _get_conversation_messages(
        self,
        db: Session,
        conversation_id: str,
        limit: int = 100
    ) -> list[Message]:
        """Get conversation messages and convert to schema format."""
        try:
            db_messages = db.query(MessageModel).filter(
                MessageModel.conversation_id == conversation_id
            ).order_by(MessageModel.created_at.asc()).limit(limit).all()

            return [self._convert_db_message_to_schema(msg) for msg in db_messages]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get messages: {str(e)}") from e

    def _update_conversation_timestamp(self, db: Session, conversation: Conversation):
        """Update conversation's updated_at timestamp."""
        try:
            conversation.updated_at = datetime.utcnow()
            db.add(conversation)
            db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            raise DatabaseError(f"Failed to update conversation timestamp: {str(e)}") from e

    def _convert_db_message_to_schema(self, db_message: MessageModel) -> Message:
        """Convert database message model to schema."""
        return Message(
            id=db_message.id,
            conversation_id=db_message.conversation_id,
            created_at=db_message.created_at,
            role=db_message.role,
            content=db_message.content,
            images=db_message.images if db_message.images is not None else [],
            tool_calls=db_message.tool_calls if db_message.tool_calls is not None else [],
            artifact=db_message.artifact,
            meta=db_message.meta
        )
