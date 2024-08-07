from fastapi import APIRouter
import datetime

from stock.models.stock_pydantic_model import (
    StockModelResponse,
    StockValues,
    PerformanceData,
    Competitor,
    MarketCap,
    StockUpdateRequest,
    StockUpdateResponse,
)

router = APIRouter(prefix="/stock")


@router.get("/{stock_symbol}", response_model=StockModelResponse)
def get_stock_data(stock_symbol: str):
    curr_date = datetime.datetime.now()
    return StockModelResponse(
        status="",
        purchased_amount=0,
        purchased_status="",
        request_data=curr_date.strptime(curr_date.strftime("%Y-%m-%d"), "%Y-%m-%d"),
        company_code=stock_symbol,
        company_name="",
        stock_values=StockValues(open=0.0, high=0.0, low=0.0, close=0.0),
        performance_data=PerformanceData(
            five_days=0.0,
            one_month=0.0,
            three_months=0.0,
            year_to_date=0.0,
            one_year=0.0,
        ),
        competitors=[Competitor(name="")],
        market_cap=MarketCap(currency="", value=0.0),
    )


@router.post("/{stock_symbol}", response_model=StockUpdateResponse, status_code=201)
def update_stock_amount(stock_symbol: str, amount_data: StockUpdateRequest):
    return StockUpdateResponse(
        message=f"{amount_data.amount} units of stock {stock_symbol} were added to your stock record"
    )
