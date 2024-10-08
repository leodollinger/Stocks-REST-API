from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.controllers.stock_controller import StockController
from app.schemas.stock_schema import (
    StockModelResponseSchema,
    StockUpdateRequestSchema,
    StockUpdateResponseSchema,
)
from shared.dependencies import get_db
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stock")


@router.get("/{stock_symbol}", response_model=StockModelResponseSchema)
def get_stock_data(
    stock_symbol: str, db: Session = Depends(get_db)
) -> StockModelResponseSchema:
    """Returns the stock data with every field of the Stock model for the given symbol.

    Args:
        stock_symbol (str): company stock code. E.g.: "aapl" or "AAPL"
        db (Session, optional): sqlalchemy session. Defaults to Depends(get_db).

    Returns:
        StockModelResponseSchema: Stock Model with every field of the Stock model
    """
    logger.debug(f"Starting {stock_symbol} on get route")
    stock_controller = StockController(stock_symbol, db)
    stock_data = stock_controller.get_stock_by_company_code()
    logger.debug(f"Finishing {stock_symbol} on get route")
    return stock_data


@router.post(
    "/{stock_symbol}", response_model=StockUpdateResponseSchema, status_code=201
)
def update_stock_amount(
    stock_symbol: str,
    amount_data: StockUpdateRequestSchema,
    db: Session = Depends(get_db),
) -> StockUpdateResponseSchema:
    """update the stock entity with the purchased amount based on received argument: “amount”. E.g.: {“amount”: 5}

    Args:
        stock_symbol (str): company stock code. E.g.: "aapl" or "AAPL"
        amount_data (StockUpdateRequestSchema): request body
        db (Session, optional): sqlalchemy session. Defaults to Depends(get_db).

    Returns:
        StockUpdateResponseSchema: Message object with name of stock and amount added
    """
    stock_controller = StockController(stock_symbol, db)
    logger.debug(f"Starting {stock_symbol} on post route, adding {amount_data.amount}")
    stock_controller.update_stock_amount_by_company_code(amount_data.amount)
    logger.debug(f"Finishing {stock_symbol} on post route")
    return StockUpdateResponseSchema(
        message=f"{amount_data.amount} units of stock {stock_symbol} were added to your stock record"
    )
