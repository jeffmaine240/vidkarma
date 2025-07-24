from fastapi import APIRouter
from .auth import auth_router
from .oauth import google_auth

router = APIRouter(prefix="/v1")

router.include_router(auth_router)
router.include_router(google_auth)