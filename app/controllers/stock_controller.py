from datetime import datetime, timedelta
from typing import List
from requests_cache.session import CachedSession
from sqlalchemy.orm import Session
from app.controllers.crawler import get_web_data
from app.models.stock_model import (
    Competitor,
    MarketCap,
    PerformanceData,
    Stock,
    StockValues,
)
from app.schemas.stock_schema import (
    MarketWatchData,
    PolygonStockData,
    StockModelResponseSchema,
    StockValuesSchema,
    PerformanceDataSchema,
    CompetitorSchema,
    MarketCapSchema,
)
from shared.exceptions import NotFound, PreconditionFailedAmount, PreconditionFailedName
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


cacheSession = CachedSession(cache_name="cache/stock", expire_after=60)


def get_stock_by_company_code(
    db: Session, company_code: str
) -> StockModelResponseSchema | None:
    """Tries to get stock info from data base, if it doesn't exist yet,
    retrieves data from polygon api and marketwatch website

    Args:
        db (Session): sqlalchemy orm Session
        company_code (str): company stock code. E.g.: "aapl" or "AAPL"

    Returns:
        StockModelResponseSchema: "Get" route stock model populated
    """
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
        stock = get_new_stock(company_code)
        insert_new_stock(db, stock)
        return stock
    else:
        competitors = get_stock_competitors_by_company_code(db, company_code)
        return format_db_stock_response(stock, competitors)


def get_stock_competitors_by_company_code(
    db: Session, company_code: str
) -> List[Competitor]:
    """Gets every competitor for a given company from data base

    Args:
        db (Session): sqlalchemy orm Session
        company_code (str): company stock code. E.g.: "aapl" or "AAPL"

    Returns:
        List[Competitor]: List with every competitor found on data base
    """
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
    """Updates the stock purchased amount for a given stock present on DB

    Args:
        db (Session): sqlalchemy orm Session
        company_code (str): company stock code. E.g.: "aapl" or "AAPL"
        amount (int): amount to add (it can be negative, if willing to decrease the purchased amount)

    Raises:
        PreconditionFailedName: the stock need to exist on the DB, if not, it
            raises a precondition error and returns 412 status
        PreconditionFailedAmount: the new stock purchased amount can't be lower
            than 0, if it is, raises a precondition error and returns returns 412 status
    """
    stock = db.query(Stock).filter(Stock.company_code.ilike(company_code)).first()
    if stock is None:
        logger.error(
            f"{company_code} does not exist on database, there for it is not possible to update it."
        )
        raise PreconditionFailedName(company_code)

    if stock.purchased_amount + amount < 0:
        logger.error(
            f"{company_code} have purchased_amount {stock.purchased_amount}, it is not possible to add {amount} to it."
        )
        raise PreconditionFailedAmount(stock.purchased_amount + amount)

    stock.purchased_amount = stock.purchased_amount + amount
    db.commit()


def get_new_stock(company_code: str) -> StockModelResponseSchema:
    """Retrieves stock info from polygon api and marketwatch website

    Args:
        company_code (str): company stock code. E.g.: "aapl" or "AAPL"

    Returns:
        StockModelResponseSchema: "Get" route stock model populated
    """
    polygon_data = get_stock_from_polygon(company_code)
    web_data = get_web_data(company_code)
    return format_scrap_stock_response(polygon_data, web_data)


def add_commit_and_refresh(db: Session, instance) -> object:
    """Insert into DB, commit and refresh the inserted object

    Args:
        db (Session): sqlalchemy orm Session
        instance (object): sqlalchemy table base model

    Returns:
        object: sqlalchemy table base model refreshed
    """
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance


def insert_new_stock(db: Session, stock_response: StockModelResponseSchema) -> None:
    """Insert new stock into database

    Args:
        db (Session): sqlalchemy orm Session
        stock_response (StockModelResponseSchema): "Get" route stock model populated
    """
    stock_values = StockValues(**stock_response.stock_values.model_dump())
    stock_values = add_commit_and_refresh(db, stock_values)

    performance_data = PerformanceData(**stock_response.performance_data.model_dump())
    performance_data = add_commit_and_refresh(db, performance_data)

    stock = Stock(
        **{
            "status": stock_response.status,
            "purchased_amount": stock_response.purchased_amount,
            "purchased_status": stock_response.purchased_status,
            "request_data": stock_response.request_data,
            "company_code": stock_response.company_code,
            "company_name": stock_response.company_name,
            "stock_values_id": stock_values.id,
            "performance_data_id": performance_data.id,
        }
    )
    stock = add_commit_and_refresh(db, stock)

    for curr_competitor in stock_response.competitors:
        market_cap = MarketCap(**curr_competitor.market_cap.model_dump())
        market_cap = add_commit_and_refresh(db, market_cap)

        competitor = Competitor(
            **{
                "name": curr_competitor.name,
                "stock_id": stock.id,
                "market_cap_id": market_cap.id,
            }
        )
        competitor = add_commit_and_refresh(db, competitor)


def format_db_stock_response(
    stock: Stock, competitors: Competitor
) -> StockModelResponseSchema:
    """Formats stock data retrieved from DB into the get route response model

    Args:
        stock (Stock): sqlalchemy table object for Stock
        competitors (Competitor): sqlalchemy table object for Competitor

    Returns:
        StockModelResponseSchema: "Get" route stock model populate
    """
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


def format_scrap_stock_response(
    polygon: PolygonStockData, market_watch: MarketWatchData
) -> StockModelResponseSchema:
    """Formats stock data retrieved from polygon api and marketwatch website into the get route response model

    Args:
        polygon (PolygonStockData): pydantic schema with polygon api data
        market_watch (MarketWatchData): pydantic schema with marketwatch website data

    Returns:
        StockModelResponseSchema: "Get" route stock model populate
    """
    return StockModelResponseSchema(
        status=polygon.status,
        purchased_amount=0,
        purchased_status="",
        request_data=polygon.from_,
        company_code=polygon.symbol,
        company_name=market_watch.company_name,
        stock_values=StockValuesSchema(
            open=polygon.open_,
            high=polygon.high,
            low=polygon.low,
            close=polygon.close,
        ),
        performance_data=market_watch.performance_data,
        competitors=market_watch.competitors,
    )


def get_stock_from_polygon(company_code: str) -> PolygonStockData:
    """Gets stock data from polygon api /open-close from two days ago (Has a 60s cache)

    Args:
        company_code (str): company stock code. E.g.: "aapl" or "AAPL"

    Raises:
        NotFound: If company can't be found on polygon api, raises NotFound error and return status 404

    Returns:
        PolygonStockData: Pydantic schema with polygon api data
    """
    twoDaysAgo = datetime.now() - timedelta(2)
    twoDaysAgoFormatted = datetime.strftime(twoDaysAgo, "%Y-%m-%d")
    url = f"https://api.polygon.io/v1/open-close/{company_code.upper()}/{twoDaysAgoFormatted}"
    response = cacheSession.request(
        "GET", url, headers={"Authorization": "Bearer bmN7i7CrzrpKqFvgbB1fEaztCwZKSUjJ"}
    )
    if response.status_code != 200:
        logger.error(
            f"{company_code} is not in the data base and was not found on the polygon api (status {response.status_code})"
        )
        raise NotFound(company_code)

    return PolygonStockData(**response.json())
