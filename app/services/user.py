from typing import Optional
from uuid import UUID
from fastapi import Depends
from psycopg2 import IntegrityError
from sqlmodel import Session, select

from app.api.dependencies.custom_exception import (
    InvalidCredentialsError,
    InvalidTokenError,
    UserAlreadyExistsError,
)
from app.db.models import User
from app.core.security import security

from app.db.session import SessionDep

from app.schemas.enums import TokenType
from app.schemas.user import UserCreate, UserLogin
from app.api.dependencies import oauth2_schema


class UserService:
    """Service class for user-related operations, including authentication and user management."""

    def __init__(self):
        self.security = security

    def get_user_by_id(self, user_id: UUID, session: Session) -> Optional[User]:
        """Retrieve a user by their UUID from the database."""
        return session.get(User, user_id)


    def get_user_by_email(self, email: str, session: Session) -> Optional[User]:
        """Retrieve a user by their email address."""
        statement = select(User).where(User.email == email)
        result = session.exec(statement)
        return result.first()


    def create_user(self, user_data: UserCreate, session: Session) -> User:
        """Create a new user in the database, ensuring no duplicates."""
        existing_user = self.get_user_by_email(user_data.email, session)
        if existing_user:
            raise UserAlreadyExistsError(
                f"User with email {user_data.email} already exists."
            )

        user = User.model_validate(user_data)  # From Pydantic v2
        user.password = self.security.hash_password(user.password)

        try:
            session.add(user)
            session.commit()
            session.refresh(user)
            return user
        except IntegrityError:
            session.rollback()
            raise UserAlreadyExistsError(
                f"User with email {user_data.email} already exists."
            )

    def authenticate_user(self, user_data: UserLogin, session: Session) -> User:
        """
        Authenticate a user based on email and password.
        Raises error if user doesn't exist or password is incorrect.
        """
        user = self.get_user_by_email(user_data.email, session)

        if not user or not self.security.verify_password(
            user_data.password, user.password
        ):
            raise InvalidCredentialsError("Invalid email or password.")

        return user

    def get_current_user(self, session: SessionDep, token: str = Depends(oauth2_schema)) -> User:
        
        """
        Retrieves the currently authenticated user from a JWT token.

        Args:
            token (str): The access token from Authorization header.
            session (Session): DB session.

        Returns:
            User: Authenticated user.

        Raises:
            InvalidTokenError: If token is invalid or user is not found.
        """
        payload = self.security.decode_token(token, token_type=TokenType.ACCESS)
        user_id = payload.get("sub")
        if not user_id:
            raise InvalidTokenError("Invalid token payload.")
        user = self.get_user_by_id(UUID(user_id), session)
        if not user:
            raise InvalidTokenError("User not found for the provided token.")
        return user


user_service = UserService()

