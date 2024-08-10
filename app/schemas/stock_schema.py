from datetime import date
from typing import List
from pydantic import BaseModel, ConfigDict, Field


class PerformanceDataSchema(BaseModel):
    five_days: float
    one_month: float
    three_months: float
    year_to_date: float
    one_year: float


class MarketCapSchema(BaseModel):
    currency: str
    value: float


class CompetitorSchema(BaseModel):
    name: str
    market_cap: MarketCapSchema


class StockValuesSchema(BaseModel):
    open: float
    high: float
    low: float
    close: float


class StockModelResponseSchema(BaseModel):
    status: str
    purchased_amount: int
    purchased_status: str
    request_data: date
    company_code: str
    company_name: str
    stock_values: StockValuesSchema
    performance_data: PerformanceDataSchema
    competitors: List[CompetitorSchema]


class StockUpdateRequestSchema(BaseModel):
    amount: int


class StockUpdateResponseSchema(BaseModel):
    message: str

class PolygonStockData(BaseModel):
    status: str
    from_: str = Field(..., alias='from')
    symbol: str
    open_: float = Field(..., alias='open')
    high: float
    low: float
    close: float
    volume: float
    afterHours: float
    preMarket: float
    model_config = ConfigDict(populate_by_name=True)

class MarketWatchData(BaseModel):
    company_name: str
    performance_data: PerformanceDataSchema
    competitors: List[CompetitorSchema]