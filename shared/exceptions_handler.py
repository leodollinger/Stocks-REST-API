from fastapi import Request
from fastapi.responses import JSONResponse
from shared.exceptions import NotFound, PreconditionFailedAmount, PreconditionFailedName


async def not_found_exception_handler(request: Request, exc: NotFound):
    return JSONResponse(
        status_code=404,
        content={"message": f"{exc.name} not found."},
    )


async def precondition_failed_name_exception_handler(
    request: Request, exc: PreconditionFailedName
):
    return JSONResponse(
        status_code=412,
        content={"message": f"Precondition failed, {exc.name} is not valid."},
    )


async def precondition_failed_amount_exception_handler(
    request: Request, exc: PreconditionFailedAmount
):
    return JSONResponse(
        status_code=412,
        content={
            "message": f"Precondition failed, {exc.name} total stock amount is not valid."
        },
    )
