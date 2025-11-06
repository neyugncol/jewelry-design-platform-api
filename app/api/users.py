"""User API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.user import UserRegister, UserLogin, Token, UserResponse, UserUpdate
from app.services.user_service import (
    UserService,
    UserAlreadyExistsError,
    InvalidCredentialsError,
    UserNotFoundError,
    UserServiceError
)
from app.utils.auth import get_current_active_user
from app.models.user import User


router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Register a new user.

    Creates a new user account with email and password.
    Returns the created user details (without password).

    Args:
        user_data: User registration data including email, password, and profile info
        db: Database session

    Returns:
        UserResponse with created user details

    Raises:
        HTTPException: 400 if user already exists, 500 for other errors
    """
    try:
        user = UserService.create_user(db, user_data)
        return user
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except UserServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Login with email and password.

    Authenticates user credentials and returns a JWT access token.

    Args:
        login_data: Login credentials (email and password)
        db: Database session

    Returns:
        Token with access_token and token_type

    Raises:
        HTTPException: 401 if credentials are invalid
    """
    user = UserService.authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token = UserService.create_access_token(data={"sub": user.id})
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current authenticated user information.

    Returns the profile of the currently authenticated user.

    Args:
        current_user: Current authenticated user from token

    Returns:
        UserResponse with current user details
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user_info(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user profile.

    Updates the profile information for the currently authenticated user.

    Args:
        user_data: User update data
        current_user: Current authenticated user from token
        db: Database session

    Returns:
        UserResponse with updated user details

    Raises:
        HTTPException: 500 if update fails
    """
    try:
        updated_user = UserService.update_user(db, current_user.id, user_data)
        return updated_user
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except UserServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_current_user(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Deactivate current user account.

    Deactivates the currently authenticated user's account.
    This does not delete the account, but prevents login.

    Args:
        current_user: Current authenticated user from token
        db: Database session

    Raises:
        HTTPException: 500 if deactivation fails
    """
    try:
        UserService.deactivate_user(db, current_user.id)
        return None
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except UserServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
