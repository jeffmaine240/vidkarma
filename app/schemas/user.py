from datetime import datetime
from typing import Optional, Union
from pydantic import BaseModel, EmailStr

from app.schemas.enums import AuthProvider

class UserCreate(BaseModel):
    """UserCreate schema for creating a new user.

    Args:
        BaseModel (_type_): Base model from Pydantic for data validation.
    """
    email: EmailStr
    password: str
    auth_provider: AuthProvider = AuthProvider.LOCAL
    
    
class OauthUserCreate(BaseModel):
    """UserCreate schema for creating a new user via oauth.

    Args:
        BaseModel (_type_): Base model from Pydantic for data validation.
    """
    email: EmailStr
    is_verified: bool = True
    auth_provider: AuthProvider
    


class RegisteredUserData(BaseModel):
    """Registration schema"""
    uuid: str
    email: EmailStr
    is_active: bool
    is_superadmin: bool
    is_verified: bool
    is_deleted: bool
    auth_provider: AuthProvider
    created_at: datetime


    
class UserLogin(UserCreate):
    """UserLogin schema for user login."""