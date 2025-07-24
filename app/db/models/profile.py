from typing import Optional
from sqlmodel import Relationship
from uuid import UUID

from ..base_model import BaseModel, Field



class UserProfile(BaseModel, table=True):
    first_name: Optional[str] = Field(default=None, nullable=True)
    last_name: Optional[str] = Field(default=None, nullable=True)
    username: str = Field(index=True, unique=True, nullable=False)
    bio: Optional[str] = Field(default=None, nullable=True)
    profile_picture_url: Optional[str] = Field(default=None, nullable=True)
    point_balance: int = Field(default=0, ge=0, nullable=False)
    user_id: UUID = Field(foreign_key="user.uuid", unique=True)
    
    user: Optional["User"] = Relationship(back_populates="profile") # type: ignore
    
    def __repr__(self):
        return f"<UserProfile(first_name={self.first_name}, last_name={self.last_name})>"
    
    
    def get_full_name(self) -> str:
        """Returns the full name of the user."""
        return f"{self.first_name or ''} {self.last_name or ''}".strip()
    