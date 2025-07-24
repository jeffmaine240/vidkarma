from typing import Optional

from sqlmodel import Relationship

from app.schemas.enums import AuthProvider
from ..base_model import BaseModel, Field


class User(BaseModel, table=True):
    """User model representing a user in the system."""
    email: str = Field(index=True, unique=True, nullable=False)
    password: Optional[str] = Field(default=None, nullable=True)
    
    is_active: bool = Field(default=True, nullable=True)
    is_verified: bool = Field(default=False, nullable=True)
    is_superadmin: bool = Field(default=False, nullable=True)
    is_deleted: bool = Field(default=False, nullable=True)
    
    auth_provider: str = Field(default=AuthProvider.LOCAL.value, nullable=True)
    
    profile: Optional["UserProfile"] = Relationship(back_populates="user") # type: ignore
    
    def __repr__(self):
        return f"<User(uuid={self.uuid}, email={self.email}, is_active={self.is_active}, is_verified={self.is_verified})>"
    
    model_config = {
        "from_attributes": True
    }