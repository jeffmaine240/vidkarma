from typing import Annotated
from fastapi import Depends
from sqlmodel import Session
from . import engine



# Session factory
def get_session():
    if not engine:
        raise RuntimeError("Database engine is not initialized.")
    with Session(engine) as session:
        yield session


# For dependency injection in routes
SessionDep = Annotated[Session, Depends(get_session)]
