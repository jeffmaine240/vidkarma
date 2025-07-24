from typing import Optional
from fastapi import HTTPException
from sqlmodel import Session

from app.db.models.user import User
from app.schemas.enums import AuthProvider
from app.schemas.oauth import UserOauthEmail
from app.schemas.user import OauthUserCreate


class GoogleOauthServices:
    """Handles database operations for Google OAuth"""

    def create(self, email_data: UserOauthEmail, session: Session) -> User:
        """
        Creates a user using information from Google OAuth2.

        Args:
            email: user email data
            session: SQLModel Session

        Returns:
            A new or existing user.
        """
        try:
            return self.create_user(
                session=session,
                user_data=OauthUserCreate(
                    email=email_data.email,
                    auth_provider=AuthProvider.GOOGLE,
                    is_verified=True
                )
            )

        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=f"OAuth user creation failed: {e}")

    def create_user(self, user_data: OauthUserCreate, session: Session) -> User:
        """
        Handles creation of a new user from Google data.

        Args:
            google_response: Dict returned by Google OAuth.
            session: SQLModel session.

        Returns:
            User: the created user.
        """

        # Create new user
        user = User(
            email=user_data.email,
            is_verified=user_data.is_verified,
            auth_provider=user_data.auth_provider
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
        

    def extract_email(self, google_response: dict) -> Optional[str]:
        """Safely extracts email from various possible Google OAuth formats."""
        if "email" in google_response:
            return google_response["email"]

        payload = google_response.get("payload", {})
        if "email" in payload:
            return payload["email"]

        emails = google_response.get("emails")
        if emails and isinstance(emails, list):
            return emails[0].get("value")

        return None


google_oauth_service = GoogleOauthServices()
