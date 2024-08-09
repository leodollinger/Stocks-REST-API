from fastapi import APIRouter, Depends
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.stock_model import (
    Competitor,
    MarketCap,
    PerformanceData,
    Stock,
    StockValues,
)
from app.schemas.stock_schema import (
    StockModelResponseSchema,
    StockValuesSchema,
    PerformanceDataSchema,
    CompetitorSchema,
    MarketCapSchema,
    StockUpdateRequestSchema,
    StockUpdateResponseSchema,
)
from shared.dependencies import get_db
from shared.exceptions import NotFound, PreconditionFailed

router = APIRouter(prefix="/stock")


@router.get("/{stock_symbol}", response_model=StockModelResponseSchema)
def get_stock_data(stock_symbol: str, db: Session = Depends(get_db)):
    stock = (
        db.query(Stock)
        .join(StockValues, Stock.stock_values_id == StockValues.id, isouter=True)
        .join(
            PerformanceData,
            Stock.performance_data_id == PerformanceData.id,
            isouter=True,
        )
        .where(Stock.company_code.ilike(stock_symbol))
        .first()
    )
    if stock is None:
        raise NotFound(stock_symbol)

    competitors = (
        db.query(Competitor)
        .join(Stock, Competitor.stock_id == Stock.id, isouter=True)
        .join(MarketCap, Competitor.market_cap_id == MarketCap.id, isouter=True)
        .where(Stock.company_code.ilike(stock_symbol))
        .all()
    )

    return format_stock_response(stock, competitors)


@router.post(
    "/{stock_symbol}", response_model=StockUpdateResponseSchema, status_code=201
)
def update_stock_amount(
    stock_symbol: str,
    amount_data: StockUpdateRequestSchema,
    db: Session = Depends(get_db),
):
    stock_id = (
        db.query(Stock)
        .filter(Stock.company_code.ilike(stock_symbol))
        .update({Stock.purchased_amount: Stock.purchased_amount + amount_data.amount})
    )
    db.commit()
    if stock_id == 0:
        raise PreconditionFailed(stock_symbol)

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


def format_stock_response(
    stock: Stock, competitors: Competitor
) -> StockModelResponseSchema:
    return StockModelResponseSchema(
        status=stock.status,
        purchased_amount=stock.purchased_amount,
        purchased_status=stock.purchased_status,
        request_data=stock.request_data,
        company_code=stock.company_code,
        company_name=stock.company_name,
        stock_values=StockValuesSchema(
            open=stock.stock_values.open,
            high=stock.stock_values.high,
            low=stock.stock_values.low,
            close=stock.stock_values.close,
        ),
        performance_data=PerformanceDataSchema(
            five_days=stock.performance_data.five_days,
            one_month=stock.performance_data.one_month,
            three_months=stock.performance_data.three_months,
            year_to_date=stock.performance_data.year_to_date,
            one_year=stock.performance_data.one_year,
        ),
        competitors=[
            CompetitorSchema(
                name=competitor.name,
                market_cap=MarketCapSchema(
                    currency=competitor.market_cap.currency,
                    value=competitor.market_cap.value,
                ),
            )
            for competitor in competitors
        ],
    )
