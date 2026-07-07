"""Authentication and registration HTTP API layer for DefenSync."""

from datetime import datetime
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from backend.api.dependencies import get_db, get_current_admin, get_current_user
from backend.core.exceptions import ResourceNotFoundError, ValidationException
from backend.database import crud
from backend.database.models import User
from backend.services.auth_service import AuthService

router = APIRouter(tags=["Authentication"])


# =============================================================================
# Request/Response Schemas (Pydantic v2)
# =============================================================================

class RegisterRequest(BaseModel):
    """Schema for user registration request."""

    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: str = Field(..., description="Unique email address")
    password: str = Field(..., min_length=8, description="User password")


class RegisterResponse(BaseModel):
    """Schema for user registration response."""

    success: bool = True
    message: str = "User registered successfully."
    username: str


class LoginRequest(BaseModel):
    """Schema for user authentication request."""

    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


class TokenResponse(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    token_type: str = "bearer"


class UserMeResponse(BaseModel):
    """Schema for returning the currently authenticated user's profile."""

    id: str
    name: str
    username: str
    email: str
    role: str
    created_at: datetime


class UserResponse(BaseModel):
    id: str
    name: str | None = None
    username: str
    email: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# Endpoints
# =============================================================================

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register_user(
    request_data: RegisterRequest,
    db: Session = Depends(get_db),
) -> RegisterResponse:
    """Create a new user account with default analyst privileges."""
    auth_service = AuthService(db)
    user = auth_service.register_user(
        username=request_data.username,
        email=request_data.email,
        password=request_data.password,
    )
    return RegisterResponse(username=user.username)


@router.post(
    "/token",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate and obtain JWT token",
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Authenticate credentials and generate a signed access token."""

    auth_service = AuthService(db)

    user = auth_service.authenticate_user(
        username=form_data.username,
        password=form_data.password,
    )

    token = auth_service.create_token(user)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
    )


@router.get(
    "/me",
    response_model=UserMeResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve current user profile",
)
def get_me(
    current_user: User = Depends(get_current_user),
) -> UserMeResponse:
    """Retrieve details of the currently authenticated active user session."""
    return UserMeResponse(
        id=current_user.id,
        name=current_user.name or current_user.username,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role.upper(),
        created_at=current_user.created_at,
    )


@router.get("/users", response_model=list[UserResponse], summary="List users (Admin Only)")
def list_users(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> list[UserResponse]:
    del current_admin
    return [
        UserResponse(
            id=user.id,
            name=user.name or user.username,
            username=user.username,
            email=user.email,
            role=user.role.upper(),
            created_at=user.created_at,
        )
        for user in crud.list_users(db)
    ]


@router.delete("/users/{user_id}", summary="Delete user (Admin Only)")
def delete_user(
    user_id: str,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    if user_id == current_admin.id:
        raise ValidationException("You cannot delete your own account.")
    deleted = crud.delete_user(db, user_id)
    if not deleted:
        raise ResourceNotFoundError(f"User '{user_id}' not found.")
    db.commit()
    return {"success": True, "message": "User deleted."}
