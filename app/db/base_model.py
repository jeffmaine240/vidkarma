from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Optional


from sqlalchemy import event



def utcnow():
    """
    Returns the current UTC time.
    """
    return datetime.now(timezone.utc)

class BaseModel(SQLModel):
    __abstract__ = True  # ✅ Prevents table creation for the base

    uuid: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        index=True
    )

    created_at: datetime = Field(
        default_factory=utcnow,
        nullable=False,
        index=True
    )

    updated_at: Optional[datetime] = Field(
        default=None,
        nullable=True,
        index=True
    )

    def model_dump(self, *args, **kwargs):
        return super().model_dump(*args, **kwargs)
    




# Automatically update `updated_at` on DB-level update
@event.listens_for(BaseModel, "before_update", propagate=True)
def update_timestamp(mapper, connection, target):
    target.updated_at = utcnow()