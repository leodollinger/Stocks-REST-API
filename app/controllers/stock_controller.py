from typing import List
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
)
from shared.exceptions import NotFound, PreconditionFailedAmount, PreconditionFailedName


def get_stock_by_company_code(db: Session, company_code: str) -> Stock | None:
    stock = (
        db.query(Stock)
        .join(StockValues, Stock.stock_values_id == StockValues.id, isouter=True)
        .join(
            PerformanceData,
            Stock.performance_data_id == PerformanceData.id,
            isouter=True,
        )
        .where(Stock.company_code.ilike(company_code))
        .first()
    )

    if stock is None:
        raise NotFound(company_code)

    return stock


def get_stock_competitors_by_company_code(
    db: Session, company_code: str
) -> List[Competitor]:
    return (
        db.query(Competitor)
        .join(Stock, Competitor.stock_id == Stock.id, isouter=True)
        .join(MarketCap, Competitor.market_cap_id == MarketCap.id, isouter=True)
        .where(Stock.company_code.ilike(company_code))
        .all()
    )


def update_stock_amount_by_company_code(
    db: Session, company_code: str, amount: int
) -> None:
    stock = db.query(Stock).filter(Stock.company_code.ilike(company_code)).first()
    if stock is None:
        raise PreconditionFailedName(company_code)

    if stock.purchased_amount + amount < 0:
        raise PreconditionFailedAmount(stock.purchased_amount + amount)

    stock.purchased_amount = stock.purchased_amount + amount
    db.commit()


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
