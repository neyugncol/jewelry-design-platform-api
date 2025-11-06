"""User service for authentication and user management."""
import uuid
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from passlib.context import CryptContext
from jose import JWTError, jwt

from app.models.user import User
from app.schemas.user import UserRegister, UserUpdate
from app.config import settings


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = getattr(settings, 'secret_key', "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


class UserServiceError(Exception):
    """Base exception for UserService errors."""
    pass


class UserAlreadyExistsError(UserServiceError):
    """Raised when trying to create a user that already exists."""
    pass


class UserNotFoundError(UserServiceError):
    """Raised when user is not found."""
    pass


class InvalidCredentialsError(UserServiceError):
    """Raised when credentials are invalid."""
    pass


class UserService:
    """Service for user authentication and management."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def decode_access_token(token: str) -> Optional[str]:
        """Decode JWT token and return user_id."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                return None
            return user_id
        except JWTError:
            return None

    @staticmethod
    def create_user(db: Session, user_data: UserRegister) -> User:
        """
        Create a new user.

        Args:
            db: Database session
            user_data: User registration data

        Returns:
            Created user

        Raises:
            UserAlreadyExistsError: If email already exists
        """
        try:
            # Check if user already exists
            existing_user = db.query(User).filter(User.email == user_data.email).first()
            if existing_user:
                raise UserAlreadyExistsError(f"User with email {user_data.email} already exists")

            # Create new user
            hashed_password = UserService.hash_password(user_data.password)
            user = User(
                id=str(uuid.uuid4()),
                email=user_data.email,
                hashed_password=hashed_password,
                name=user_data.name,
                gender=user_data.gender,
                age=user_data.age,
                marital_status=user_data.marital_status,
                segment=user_data.segment,
                region=user_data.region,
                nationality=user_data.nationality,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        except UserAlreadyExistsError:
            raise
        except IntegrityError as e:
            db.rollback()
            raise UserAlreadyExistsError(f"User with email {user_data.email} already exists") from e
        except SQLAlchemyError as e:
            db.rollback()
            raise UserServiceError(f"Failed to create user: {str(e)}") from e

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """
        Authenticate a user with email and password.

        Args:
            db: Database session
            email: User email
            password: User password

        Returns:
            User if authentication successful, None otherwise
        """
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
        if not UserService.verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user

    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email."""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def update_user(db: Session, user_id: str, user_data: UserUpdate) -> User:
        """
        Update user profile.

        Args:
            db: Database session
            user_id: User ID
            user_data: User update data

        Returns:
            Updated user

        Raises:
            UserNotFoundError: If user not found
        """
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise UserNotFoundError(f"User {user_id} not found")

            # Update fields if provided
            update_data = user_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(user, field, value)

            user.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(user)
            return user
        except UserNotFoundError:
            raise
        except SQLAlchemyError as e:
            db.rollback()
            raise UserServiceError(f"Failed to update user: {str(e)}") from e

    @staticmethod
    def deactivate_user(db: Session, user_id: str) -> User:
        """
        Deactivate a user account.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Deactivated user

        Raises:
            UserNotFoundError: If user not found
        """
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise UserNotFoundError(f"User {user_id} not found")

            user.is_active = False
            user.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(user)
            return user
        except UserNotFoundError:
            raise
        except SQLAlchemyError as e:
            db.rollback()
            raise UserServiceError(f"Failed to deactivate user: {str(e)}") from e
