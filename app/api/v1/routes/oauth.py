from datetime import timedelta
from urllib.parse import urlencode
from fastapi.responses import RedirectResponse
import requests
from fastapi import APIRouter, Depends, Request, status

from app.api.dependencies.custom_exception import GoogleInitiationError, OauthError, ServerError
from app.api.dependencies.response import success_response
from app.core.config import Config
from app.db.models.user import User
from app.schemas.enums import Environment, TokenType
from app.schemas.responses.oauth import EnvironmentParams, OAuthResponse
from app.schemas.responses.user import UserResponse
from app.schemas.token import TokenCreate
from app.schemas.user import RegisteredUserData
from app.services.user import user_service
from app.services.oauth import google_oauth_service
from app.core.security import security
from app.db.session import SessionDep
from app.schemas.oauth import OAuthToken, UserOauthEmail
from app.utils.logger import get_logger



logger = get_logger(__name__)
google_auth = APIRouter(prefix="/oauth", tags=["Oauth"])


async def handle_google_login(profile_data: dict, db: SessionDep) -> tuple[User, bool]:
    """
    Shared logic to handle Google login.
    Returns (user, is_new_user)
    """
    email = google_oauth_service.extract_email(google_response=profile_data)
    if not email and "sub" in profile_data:
        email = f"{profile_data['sub']}@placeholder.google.com"

    user = user_service.get_user_by_email(session=db, email=email)
    is_new_user = False

    if not user:
        user = google_oauth_service.create(session=db, email_data=UserOauthEmail(email=email))
        is_new_user = True

    return user, is_new_user


@google_auth.post("/google")
async def google_login(request: Request, token_request: OAuthToken, db: SessionDep):
    profile_endpoint = f"https://www.googleapis.com/oauth2/v3/tokeninfo?id_token={token_request.id_token}"
    profile_response = requests.get(profile_endpoint)

    if profile_response.status_code != 200:
        raise OauthError(
            message="Google Authentication failed",
            errors={"error": "Invalid ID token"}
        )

    profile_data = profile_response.json()
    user, created = await handle_google_login(profile_data, db)

    response = success_response(
        status_code=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        message="Login successful",
        data=UserResponse(
            user=RegisteredUserData(**user.to_dict()),
            access_token=security.create_token(
                token_data=TokenCreate(
                    user_id=str(user.uuid),
                    token_type=TokenType.ACCESS
                )
            ),
        ),
    )

    response.set_cookie(
        key="refresh_token",
        value=security.create_token(
            token_data=TokenCreate(
                user_id=str(user.uuid),
                token_type=TokenType.ACCESS
            )
        ),
        expires=timedelta(days=60),
        httponly=True,
        secure=True,
        samesite="lax",
    )

    return response


@google_auth.get("/google/initiate")
async def initiate_google_auth(request_params: EnvironmentParams = Depends()):
    try:
        client_id = Config.GOOGLE_CLIENT_ID
        redirect_uri = Config.GOOGLE_REDIRECT_URI

        if not client_id:
            raise ServerError(
                message="Google Initiation failed",
                errors={"error": "Google Client ID is not configured"}
            )

        if not redirect_uri:
            raise ServerError(
                message="Google Initiation failed",
                errors={"error": "Redirect URI is not configured"}
            )

        if not request_params.environment:
            raise GoogleInitiationError(
                message="Google Initiation failed",
                errors={"error": "environment parameter not included"}
            )

        env = Environment(request_params.environment)
        state = f"{security.generate_random_hex()}:{env.value}"

        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        query_string = urlencode({
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
        })

        auth_url = f"{base_url}?{query_string}"

        if request_params.return_json:
            return success_response(
                status_code=status.HTTP_200_OK,
                message="Google OAuth URL generated",
                data=OAuthResponse(
                    auth_url=auth_url, state=state, redirect_uri=redirect_uri
                ),
            )

        return RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)

    except Exception as e:
        raise ServerError(
            message="Google Initiation failed",
            errors={"error": str(e)}
        )


@google_auth.get("/google/callback")
async def google_callback(request: Request, db: SessionDep):
    query_params = dict(request.query_params)
    code = query_params.get("code")
    state = query_params.get("state", "")

    redirect_url = (
        "http://localhost:3000" if "redirect_local" in state else Config.frontend_url
    )

    if not code:
        if "local" in state:
            redirect_url = "http://localhost:3000/"
        elif "staging" in state:
            redirect_url = "https://staging.vidkarma.ad/"
        elif "prod" in state:
            redirect_url = "https://vidkarma.ad/"
        else:
            redirect_url = "https://vidkarma.ad/"
        return RedirectResponse(url=redirect_url, status_code=302)

    try:
        token_url = "https://oauth2.googleapis.com/token"
        token_response = requests.post(
            token_url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": Config.GOOGLE_REDIRECT_URI,
                "client_id": Config.GOOGLE_CLIENT_ID,
                "client_secret": Config.GOOGLE_CLIENT_SECRET,
            },
        )

        if token_response.status_code != 200:
            raise OauthError(
                message="Google Authentication failed",
                errors={"error": "Failed to exchange authorization code"}
            )

        token_data = token_response.json()
        id_token = token_data.get("id_token")

        profile_endpoint = f"https://www.googleapis.com/oauth2/v3/tokeninfo?id_token={id_token}"
        profile_response = requests.get(profile_endpoint)

        if profile_response.status_code != 200:
            raise OauthError(
                message="Google Authentication failed",
                errors={"error": "Invalid ID token"}
            )

        profile_data = profile_response.json()
        user, _ = await handle_google_login(profile_data, db)

        if "local" in state:
            frontend_url = "http://localhost:3000/auth/callback"
        elif "staging" in state:
            frontend_url = "https://staging.vidkarma.ad/auth/callback"
        elif "prod" in state:
            frontend_url = "https://vidkarma/auth/callback"
        else:
            frontend_url = Config.frontend_url
            
        access_token=security.create_token(
            token_data=TokenCreate(
                user_id=str(user.uuid),
                token_type=TokenType.ACCESS
            )
        )
        
        refresh_token=security.create_token(
            token_data=TokenCreate(
                user_id=str(user.uuid),
                token_type=TokenType.REFRESH
            )
        )

        redirect_url = f"{frontend_url}?auth_success=true&access_token={access_token}&id_token={id_token}"
        response = RedirectResponse(url=redirect_url, status_code=302)

        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            expires=timedelta(days=30),
            httponly=True,
            secure=True,
            samesite="none",
        )

        response.set_cookie(
            key="id_token",
            value=id_token,
            expires=timedelta(hours=1),
            httponly=True,
            secure=True,
            samesite="none",
        )

        return response

    except Exception as e:
        logger.error(f"Google callback error: {str(e)}", exc_info=True)
        error_redirect_url = f"{Config.frontend_url}/auth/callback?auth_success=false"
        return RedirectResponse(url=error_redirect_url, status_code=status.HTTP_302_FOUND)


