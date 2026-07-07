"""
Authentication business logic service for DefenSync.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.core.exceptions import (
    AuthenticationError,
    DatabaseException,
    ValidationException,
)
from backend.core.logging import get_logger
from backend.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from backend.database.crud import (
    create_user,
    get_user_by_email,
    get_user_by_username,
)
from backend.database.models import User

logger = get_logger(__name__)


class AuthService:
    """
    Business logic for authentication and user registration.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def register_user(
        self,
        username: str,
        email: str,
        password: str,
        role: str = "ANALYST",
    ) -> User:

        username = username.strip()
        email = email.strip().lower()

        if not username:
            raise ValidationException("Username cannot be empty.")

        if not email:
            raise ValidationException("Email cannot be empty.")

        if not password:
            raise ValidationException("Password cannot be empty.")

        role = role.strip().upper()
        if role not in {"ADMIN", "ANALYST"}:
            raise ValidationException("Invalid user role.")

        if get_user_by_username(self.db, username=username):
            raise ValidationException("Username already exists.")

        if get_user_by_email(self.db, email=email):
            raise ValidationException("Email already exists.")

        password_hash = hash_password(password)

        try:
            user = create_user(
                self.db,
                username=username,
                email=email,
                password=password_hash,
                role=role,
            )
            self.db.commit()
            return user
        except Exception as exc:
            self.db.rollback()
            logger.exception("Failed to register user: %s", username)
            raise DatabaseException("Failed to register user.") from exc

    def authenticate_user(
        self,
        username: str,
        password: str,
    ) -> User:

        user = get_user_by_username(
            self.db,
            username=username,
        )

        if user is None:
            raise AuthenticationError(
                "Invalid username or password."
            )

        if not verify_password(
            password,
            user.password_hash or user.hashed_password,
        ):
            raise AuthenticationError(
                "Invalid username or password."
            )

        return user

    def create_token(
        self,
        user: User,
    ) -> str:

        return create_access_token(
            {
                "sub": user.username,
                "role": user.role,
            }
        )
