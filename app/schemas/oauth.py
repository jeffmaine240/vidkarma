from fastapi import Query
from pydantic import BaseModel, EmailStr


class OAuthToken(BaseModel):
    id_token: str


class UserOauthEmail(BaseModel):
    email: EmailStr
    


