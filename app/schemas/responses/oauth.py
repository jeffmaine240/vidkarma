from datetime import datetime
from typing import Optional, Union

from fastapi import Query
from pydantic import BaseModel, EmailStr, Field

from app.schemas.enums import Environment




# class EnvironmentParams:
class EnvironmentParams:
    """Query parameters for environment and response format control."""

    def __init__(
        self,
        environment: Environment | None = Query(
            default=None,
            description="Target environment: one of local, staging, prod",
            examples=["local", "staging", "prod"],
        ),
        return_json: bool = Query(
            default=False,
            description="Format: True for JSON, False for native",
        ),
    ):
        self.environment = environment
        self.return_json = return_json

class OAuthResponse(BaseModel):
    auth_url: str
    state: str
    redirect_uri: str | None = None
