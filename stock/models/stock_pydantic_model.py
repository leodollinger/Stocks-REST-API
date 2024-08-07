from datetime import datetime
from typing import List
from pydantic import BaseModel


class PerformanceData(BaseModel):
    five_days: float
    one_month: float
    three_months: float
    year_to_date: float
    one_year: float


class Competitor(BaseModel):
    name: str


class MarketCap(BaseModel):
    currency: str
    value: float


class StockValues(BaseModel):
    open: float
    high: float
    low: float
    close: float


class StockModelResponse(BaseModel):
    status: str
    purchased_amount: int
    purchased_status: str
    request_data: datetime
    company_code: str
    company_name: str
    stock_values: StockValues
    performance_data: PerformanceData
    competitors: List[Competitor]
    market_cap: MarketCap


class StockUpdateRequest(BaseModel):
    amount: float


class StockUpdateResponse(BaseModel):
    message: str
