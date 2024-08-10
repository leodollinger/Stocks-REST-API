import uvicorn
from fastapi import FastAPI

from shared.database import Base, engine
from app.routers.stock_router import router

from app.models.stock_model import *
from shared.exceptions import NotFound, PreconditionFailedAmount, PreconditionFailedName
from shared.exceptions_handler import (
    not_found_exception_handler,
    precondition_failed_name_exception_handler,
    precondition_failed_amount_exception_handler,
)

app = FastAPI()

app.include_router(router)
app.add_exception_handler(NotFound, not_found_exception_handler)
app.add_exception_handler(
    PreconditionFailedName, precondition_failed_name_exception_handler
)
app.add_exception_handler(
    PreconditionFailedAmount, precondition_failed_amount_exception_handler
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
