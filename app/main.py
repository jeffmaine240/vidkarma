from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.exceptions import HTTPException
from sqlmodel import Session, text
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

import uvicorn


from app.utils.limiter import limiter
from app.utils.logger import get_logger
from app.core.config import Config
from app.api.v1.routes import router
from app.db import engine
from app.api.dependencies.response import error_response
from app.api.dependencies.custom_exception import (
    create_exception_handler,
    create_rate_limit_exception_handler,
    GoogleOAuthConfigError,
    UserAlreadyExistsError,
    InvalidCredentialsError,
    InvalidTokenError,
    GoogleInitiationError,
    ServerError,
    OauthError
)

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("FastAPI server is starting...")
    yield
    logger.info("FastAPI server is shutting down...")
    

app = FastAPI(
    debug=Config.DEBUG, 
    title=Config.APP_NAME,
    version=Config.APP_VERSION,
    description=Config.APP_DESCRIPTION,
    lifespan=lifespan,
)

app.state.limiter = limiter
    
@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    """Basic check that the app is alive."""
    return {"status": "alive"}


@app.get("/readiness", status_code=status.HTTP_200_OK)
def readiness_check():
    """Deep check that the app is ready (DB is reachable)."""
    try:
        with Session(engine) as session:
            session.exec(text('SELECT 1'))
            print("done")
        return {"status": "ready"}
    
    except Exception as e:
        logger.error("Readiness check failed: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Readiness check failed: {str(e)}"
        )


app.add_exception_handler(
    exc_class_or_status_code= GoogleOAuthConfigError,
    handler=create_exception_handler(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        default_message="Google OAuth configuration error occurred"
    ),
)

app.add_exception_handler(
    exc_class_or_status_code=UserAlreadyExistsError,
    handler=create_exception_handler(
        status_code=status.HTTP_409_CONFLICT,
        default_message="A user with this email already exists."
    ),
)

app.add_exception_handler(
    exc_class_or_status_code=InvalidCredentialsError,
    handler=create_exception_handler(
        status_code=status.HTTP_401_UNAUTHORIZED,
        default_message="Invalid credentials provided."
    ),
)

app.add_exception_handler(
    exc_class_or_status_code=InvalidTokenError,
    handler=create_exception_handler(
        status_code=status.HTTP_401_UNAUTHORIZED,
        default_message="Invalid or expired token."
    ),
)

app.add_exception_handler(
    exc_class_or_status_code=GoogleInitiationError,
    handler=create_exception_handler(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        default_message="Invalid or expired token."
    ),
)

app.add_exception_handler(
    exc_class_or_status_code=ServerError,
    handler=create_exception_handler(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        default_message="Internal Server Error"
    ),
)
app.add_exception_handler(
    exc_class_or_status_code=OauthError,
    handler=create_exception_handler(
        status_code=status.HTTP_401_UNAUTHORIZED,
        default_message="Authentication failed"
    ),
)
app.add_exception_handler(
    exc_class_or_status_code=RateLimitExceeded, 
    handler=create_rate_limit_exception_handler(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        default_message="Too many requests, please try again later."
    ),
)

app.include_router(router=router, prefix="/api")
app.add_middleware(SessionMiddleware, secret_key=Config.APP_SECRET_KEY)


# Set up allowed origins
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "https://vidkarma.ad",
    "https://www.vidkarma.ad",
    "https://staging.api.vidkarma.ad",
    "https://staging.vidkarma.ad",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=7001,
        reload=True if Config.DEBUG else False
    ) 
    
    