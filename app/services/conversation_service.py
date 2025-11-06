"""Conversation service for managing conversations and messages."""
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.schemas.conversation import ConversationCreate


class ConversationService:
    """Service for conversation operations."""

    @staticmethod
    def create_conversation(
        db: Session,
        conversation_data: ConversationCreate,
        user_id: str
    ) -> Conversation:
        """Create a new conversation for the given user."""
        try:
            conversation = Conversation(
                id=str(uuid.uuid4()),
                user_id=user_id,
                title=conversation_data.title,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            return conversation
        except SQLAlchemyError as e:
            db.rollback()
            raise Exception(f"Failed to create conversation: {str(e)}") from e

    @staticmethod
    def get_conversation(
        db: Session,
        conversation_id: str
    ) -> Optional[Conversation]:
        """Get conversation by ID."""
        return db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

    @staticmethod
    def get_conversation_with_messages(
        db: Session,
        conversation_id: str
    ) -> Optional[Conversation]:
        """Get conversation with all messages."""
        return db.query(Conversation).options(
            joinedload(Conversation.messages)
        ).filter(
            Conversation.id == conversation_id
        ).first()

    @staticmethod
    def list_conversations(
        db: Session,
        user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[Conversation], int]:
        """List conversations with pagination."""
        query = db.query(Conversation)

        if user_id:
            query = query.filter(Conversation.user_id == user_id)

        total = query.count()
        conversations = query.order_by(
            Conversation.updated_at.desc()
        ).limit(limit).offset(offset).all()

        return conversations, total

    @staticmethod
    def add_message(
        db: Session,
        conversation_id: str,
        role: str,
        content: str,
        images: Optional[List[str]] = None,
        tool_calls: Optional[List[dict]] = None,
        artifact: Optional[dict] = None,
        meta: Optional[dict] = None
    ) -> Message:
        """Add a message to a conversation."""
        try:
            message = Message(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                role=role,
                content=content,
                images=images,
                tool_calls=tool_calls,
                artifact=artifact,
                meta=meta,
                created_at=datetime.utcnow()
            )
            db.add(message)
            db.commit()
            db.refresh(message)

            # Update conversation's updated_at
            conversation = db.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()
            if conversation:
                conversation.updated_at = datetime.utcnow()
                db.add(conversation)
                db.commit()

            return message
        except SQLAlchemyError as e:
            db.rollback()
            raise Exception(f"Failed to add message: {str(e)}") from e

    @staticmethod
    def get_conversation_messages(
        db: Session,
        conversation_id: str,
        limit: int = 100
    ) -> List[Message]:
        """Get messages for a conversation."""
        return db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.asc()).limit(limit).all()

    @staticmethod
    def delete_conversation(
        db: Session,
        conversation_id: str
    ) -> bool:
        """Delete a conversation and all its messages."""
        try:
            conversation = db.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()
            if conversation:
                db.delete(conversation)
                db.commit()
                return True
            return False
        except SQLAlchemyError as e:
            db.rollback()
            raise Exception(f"Failed to delete conversation: {str(e)}") from e
