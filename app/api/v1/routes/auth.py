from datetime import timedelta
from fastapi import Depends, Request, Response, status, APIRouter
from fastapi.responses import JSONResponse
import logging

from app.api.dependencies.custom_exception import InvalidTokenError
from app.core.security import security
from app.db.session import SessionDep
from app.api.dependencies.response import success_response
from app.db.models import User
from app.schemas.enums import TokenType
from app.schemas.responses.user import UserResponse
from app.schemas.user import RegisteredUserData, UserCreate, UserLogin
from app.services.user import user_service
from app.schemas.token import AccessTokenDetails, Token, TokenCreate, TokenDetails

from app.utils.limiter import limiter

# Setup logger
logger = logging.getLogger("auth")
logging.basicConfig(level=logging.INFO)


auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user_schema: UserCreate, db: SessionDep):
    user = user_service.create_user(session=db, user_data=user_schema)

    logger.info(f"User {user.email} registered successfully")

    response = success_response(
        status_code=status.HTTP_201_CREATED,
        message="User created successfully",
        data=UserResponse(
            user=RegisteredUserData(**user.to_dict()),
            access_token=security.create_token(
                token_data=TokenCreate(user_id=user.uuid, token_type=TokenType.ACCESS)
            )
        ),
    )

    response.set_cookie(
        key="refresh_token",
        value=security.create_token(
            token_data=TokenCreate(user_id=user.uuid, token_type=TokenType.REFRESH)
        ),
        expires=timedelta(days=60),
        httponly=True,
        secure=True,
        samesite="lax",
    )

    return response


@auth_router.post("/login", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
def login(request: Request, user_data: UserLogin, db: SessionDep):
    
    user = user_service.authenticate_user(user_data=user_data, session=db)
    logger.info(f"User {user.email} logged in successfully")

    response = success_response(
        status_code=status.HTTP_200_OK,
        message="Login successful",
        data=UserResponse(
            user=RegisteredUserData(**user.to_dict()),
            access_token=security.create_token(
                token_data=TokenCreate(user_id=user.uuid, token_type=TokenType.ACCESS)
            )
        )
    )

    response.set_cookie(
        key="refresh_token",
        value=security.create_token(
            token_data=TokenCreate(user_id=user.uuid, token_type=TokenType.REFRESH)
        ),
        expires=timedelta(days=60),
        httponly=True,
        secure=True,
        samesite="lax",
    )

    return response


@auth_router.post("/refresh-access-token", status_code=status.HTTP_200_OK, response_model=None)
@limiter.limit("10/minute")
def refresh_access_token(request: Request, current_user: User = Depends(user_service.get_current_user)):
    current_refresh_token = request.cookies.get("refresh_token")
    if not current_refresh_token or not security.is_refresh_token_active(
        data=Token(token=current_refresh_token)
    ):
        logger.warning("Invalid or expired refresh token during refresh attempt")
        raise InvalidTokenError(detail="Invalid or expired refresh token")

    access_token, refresh_token = security.refresh_access_token(current_refresh_token=current_refresh_token)

    logger.info(f"Token refreshed for user {current_user.uuid}")

    response = success_response(
        status_code=status.HTTP_200_OK,
        message="Tokens refreshed successfully",
        data=AccessTokenDetails(
            access_token=TokenDetails(
                token=access_token,
                token_type=TokenType.ACCESS
            )
        ),
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        expires=timedelta(days=30),
        httponly=True,
        secure=True,
        samesite="lax",
    )

    return response


@auth_router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(user_service.get_current_user),
):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        security.redis_client.setex(
            f"blacklisted_token:{refresh_token}", timedelta(days=30), "blacklisted"
        )
        logger.info(f"Refresh token for user {current_user.uuid} blacklisted")

    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=True,
    )

    return success_response(
        status_code=status.HTTP_200_OK,
        message="User Logged out Successfully",
    )
