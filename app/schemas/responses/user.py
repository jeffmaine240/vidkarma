from pydantic import BaseModel
from ..user import RegisteredUserData

class UserResponse(BaseModel):
    user: RegisteredUserData
    access_token: str
    