import uvicorn
from fastapi import FastAPI

from shared.database import Base, engine
from app.routers.stock_router import router

from app.models.stock_model import *
from shared.exceptions import NotFound, PreconditionFailed
from shared.exceptions_handler import (
    not_found_exception_handler,
    precondition_failed_exception_handler,
)

app = FastAPI()

app.include_router(router)
app.add_exception_handler(NotFound, not_found_exception_handler)
app.add_exception_handler(PreconditionFailed, precondition_failed_exception_handler)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
