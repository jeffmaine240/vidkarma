from typing import Annotated, Optional, Union

from fastapi import APIRouter, Body, Depends, Query, Request, status
from fastapi.encoders import jsonable_encoder
from sqlmodel import Session

from app.db.session import SessionDep
from app.api.dependencies.response import error_response, success_response
from app.db.models import User
from app.services.user import user_service

user_router = APIRouter(prefix="/users", tags=["users"])


@user_router.get("/me")
def get_current_user_details(
    request: Request,
    db: Session = SessionDep,
    current_user: User = Depends(user_service.get_current_user),
):
    """
    Get current user details.

    Args:
        request (Request): The HTTP request.
        db (Session): Database session.
        current_user (User): The currently authenticated user.

    Returns:
        CurrentUserDetailResponse: The current user's details.
    """
    return success_response(
        status_code=status.HTTP_200_OK,
        message="User details retrieved successfully",
        data=jsonable_encoder(
            current_user,
            exclude=[
                "password",
                "is_deleted",
                "updated_at",
            ],
        ),
    )


@user_router.delete("/me", status_code=status.HTTP_200_OK)
async def delete_account(
    request: Request,
    db: Session = SessionDep,
    current_user: User = Depends(user_service.get_current_user),
):
    """
    Delete current user account.

    Args:
        request (Request): The HTTP request.
        db (Session): Database session.
        current_user (User): The currently authenticated user.

    Returns:
        StandardResponse: Success message.
    """
    # Delete current user
    # user_service.delete(db=db)

    return success_response(
        status_code=status.HTTP_200_OK,
        message="User deleted successfully",
    )



@user_router.get(
    "/{user_id}"
)
def get_user_by_id(
    user_id: str,
    db: Session = SessionDep,
    current_user: User = Depends(user_service.get_current_user),
):
    """
    Get a user by ID.

    Args:
        user_id (str): The ID of the user to retrieve.
        db (Session): Database session.
        current_user (User): The currently authenticated user.

    Returns:
        UserDetailResponse: The user details.
    """
    return user_service.get_user_by_id(session=db, user_id=user_id)


# @user_router.patch("/me/password", status_code=status.HTTP_200_OK)
# def change_password(
#     request: ChangePasswordSchema,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(user_service.get_current_user),
# ):
#     """
#     Change current user's password.

#     Args:
#         request (ChangePasswordSchema): Password change data.
#         db (Session): Database session.
#         current_user (User): The currently authenticated user.

#     Returns:
#         StandardResponse: Success message.
#     """
#     user_service.change_password(
#         old_password=request.old_password,
#         new_password=request.new_password,
#         confirm_new_password=request.confirm_new_password,
#         user=current_user,
#         db=db,
#     )

#     return success_response(
#         status_code=status.HTTP_200_OK, message="Password changed successfully!!"
#     )


