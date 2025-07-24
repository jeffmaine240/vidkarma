from typing import Literal
from uuid import UUID
from pydantic import BaseModel

from app.schemas.enums import TokenType





class TokenData(BaseModel):
    """ Data to be encrypted """
    user_id: str


class TokenCreate(TokenData):
    """Schema for creating a token."""
    user_id: str
    token_type: TokenType


class Token(BaseModel):
    """Schema for refresh token data."""
    token: str


class TokenDetails(Token):
    """Details about the token"""
    token_type: TokenType
    
class AccessTokenDetails(BaseModel):
    access_token: TokenDetails