from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.controllers.stock_controller import *
from app.models.stock_model import (
    Competitor,
    MarketCap,
    PerformanceData,
    Stock,
    StockValues,
)
from app.schemas.stock_schema import (
    StockModelResponseSchema,
    StockUpdateRequestSchema,
    StockUpdateResponseSchema,
)
from shared.dependencies import get_db
from shared.exceptions import NotFound, PreconditionFailedName

router = APIRouter(prefix="/stock")


@router.get("/{stock_symbol}", response_model=StockModelResponseSchema)
def get_stock_data(stock_symbol: str, db: Session = Depends(get_db)):
    stock = get_stock_by_company_code(db, stock_symbol)
    competitors = get_stock_competitors_by_company_code(db, stock_symbol)

    return format_stock_response(stock, competitors)


@router.post(
    "/{stock_symbol}", response_model=StockUpdateResponseSchema, status_code=201
)
def update_stock_amount(
    stock_symbol: str,
    amount_data: StockUpdateRequestSchema,
    db: Session = Depends(get_db),
):
    update_stock_amount_by_company_code(db, stock_symbol, amount_data.amount)

    return StockUpdateResponseSchema(
        message=f"{amount_data.amount} units of stock {stock_symbol} were added to your stock record"
    )


@router.put("/init")
def init_stock(db: Session = Depends(get_db)):
    stock_values = StockValues(
        **{"open": 205.3, "high": 209.99, "low": 201.07, "close": 207.23}
    )
    db.add(stock_values)

    performance_data = PerformanceData(
        **{
            "five_days": -5.52,
            "one_month": -9.94,
            "three_months": 14.82,
            "year_to_date": 8.98,
            "one_year": 17.75,
        }
    )
    db.add(performance_data)

    market_cap = MarketCap(**{"currency": "$2.97T", "value": -0.30})
    db.add(market_cap)

    stock = Stock(
        **{
            "status": "OK",
            "purchased_amount": 0,
            "purchased_status": "OK",
            "request_data": "2024-08-06",
            "company_code": "AAPL",
            "company_name": "Apple Inc.",
            "stock_values_id": 1,
            "performance_data_id": 1,
        }
    )
    db.add(stock)

    competitor = Competitor(
        **{"name": "Microsoft Corp.", "stock_id": 1, "market_cap_id": 1}
    )
    db.add(competitor)

    db.commit()

    return "initialized"
