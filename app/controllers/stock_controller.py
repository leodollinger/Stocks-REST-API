from datetime import datetime, timedelta
import sys
from typing import List
from requests_cache.session import CachedSession
from sqlalchemy.orm import Session
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
from playwright.sync_api import sync_playwright
from functools import cache
import random

if sys.platform.startswith("linux"):
    from xvfbwrapper import Xvfb

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


cacheSession = CachedSession(cache_name="cache/stock", expire_after=60)


class StockController:
    def __init__(self, company_code: str, db: Session):
        """initializes the StockController class

        Args:
            company_code (str): company stock code. E.g.: "aapl" or "AAPL"
            db (Session): sqlalchemy orm Session
        """
        self.company_code = company_code
        self.db = db

    def get_stock_by_company_code(self) -> StockModelResponseSchema | None:
        """Tries to get stock info from data base, if it doesn't exist yet,
        retrieves data from polygon api and marketwatch website

        Returns:
            StockModelResponseSchema: "Get" route stock model populated
        """
        stock = (
            self.db.query(Stock)
            .join(StockValues, Stock.stock_values_id == StockValues.id, isouter=True)
            .join(
                PerformanceData,
                Stock.performance_data_id == PerformanceData.id,
                isouter=True,
            )
            .where(Stock.company_code.ilike(self.company_code))
            .first()
        )

        if stock is None:
            stock = self.get_new_stock()
            self.insert_new_stock(stock)
            return stock
        else:
            competitors = self.get_stock_competitors_by_company_code()
            return self.format_db_stock_response(stock, competitors)

    def get_stock_competitors_by_company_code(self) -> List[Competitor]:
        """Gets every competitor for a given company from data base

        Returns:
            List[Competitor]: List with every competitor found on data base
        """
        return (
            self.db.query(Competitor)
            .join(Stock, Competitor.stock_id == Stock.id, isouter=True)
            .join(MarketCap, Competitor.market_cap_id == MarketCap.id, isouter=True)
            .where(Stock.company_code.ilike(self.company_code))
            .all()
        )

    def update_stock_amount_by_company_code(self, amount: int) -> None:
        """Updates the stock purchased amount for a given stock present on DB

        Args:
            amount (int): amount to add (it can be negative, if willing to decrease the purchased amount)

        Raises:
            PreconditionFailedName: the stock need to exist on the DB, if not, it
                raises a precondition error and returns 412 status
            PreconditionFailedAmount: the new stock purchased amount can't be lower
                than 0, if it is, raises a precondition error and returns returns 412 status
        """
        stock = (
            self.db.query(Stock).filter(Stock.company_code.ilike(self.company_code)).first()
        )
        if stock is None:
            logger.error(
                f"{self.company_code} does not exist on database, there for it is not possible to update it."
            )
            raise PreconditionFailedName(self.company_code)

        if stock.purchased_amount + amount < 0:
            logger.error(
                f"{self.company_code} have purchased_amount {stock.purchased_amount}, it is not possible to add {amount} to it."
            )
            raise PreconditionFailedAmount(stock.purchased_amount + amount)

        stock.purchased_amount = stock.purchased_amount + amount
        self.db.commit()

    def get_new_stock(self) -> StockModelResponseSchema:
        """Retrieves stock info from polygon api and marketwatch website

        Returns:
            StockModelResponseSchema: "Get" route stock model populated
        """
        polygon_data = self.get_stock_from_polygon()
        web_data = self.get_market_watch()
        return self.format_scrap_stock_response(polygon_data, web_data)

    def add_commit_and_refresh(self, instance: object) -> object:
        """Insert into DB, commit and refresh the inserted object

        Args:
            instance (object): sqlalchemy table base model

        Returns:
            object: sqlalchemy table base model refreshed
        """
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def insert_new_stock(
        self, stock_response: StockModelResponseSchema
    ) -> None:
        """Insert new stock into database

        Args:
            stock_response (StockModelResponseSchema): "Get" route stock model populated
        """
        stock_values = StockValues(**stock_response.stock_values.model_dump())
        stock_values = self.add_commit_and_refresh(stock_values)

        performance_data = PerformanceData(
            **stock_response.performance_data.model_dump()
        )
        performance_data = self.add_commit_and_refresh(performance_data)

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
        stock = self.add_commit_and_refresh(stock)

        for curr_competitor in stock_response.competitors:
            market_cap = MarketCap(**curr_competitor.market_cap.model_dump())
            market_cap = self.add_commit_and_refresh(market_cap)

            competitor = Competitor(
                **{
                    "name": curr_competitor.name,
                    "stock_id": stock.id,
                    "market_cap_id": market_cap.id,
                }
            )
            competitor = self.add_commit_and_refresh(competitor)

    def format_db_stock_response(
        self, stock: Stock, competitors: Competitor
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
        self, polygon: PolygonStockData, market_watch: MarketWatchData
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

    def get_stock_from_polygon(self) -> PolygonStockData:
        """Gets stock data from polygon api /open-close on day 2024-08-09 (Has a 60s cache)

        Raises:
            NotFound: If company can't be found on polygon api, raises NotFound error and return status 404

        Returns:
            PolygonStockData: Pydantic schema with polygon api data
        """
        url = f"https://api.polygon.io/v1/open-close/{self.company_code.upper()}/2024-08-09"
        response = cacheSession.request(
            "GET",
            url,
            headers={"Authorization": "Bearer bmN7i7CrzrpKqFvgbB1fEaztCwZKSUjJ"},
        )
        if response.status_code != 200:
            logger.error(
                f"{self.company_code} is not in the data base and was not found on the polygon api (status {response.status_code})"
            )
            raise NotFound(self.company_code)

        return PolygonStockData(**response.json())

    @cache
    def get_market_watch(self) -> MarketWatchData:
        """Scraps MarketWatch website and gets data on given stock

        Returns:
            MarketWatchData: pydantic schema with marketwatch website data. If process fails, return empty version of schema
        """
        if sys.platform.startswith("linux"):
            vdisplay = Xvfb()
            vdisplay.start()
        try:
            logger.debug(f"starting crawler for stock {self.company_code}")
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            ]
            playwright = sync_playwright().start()
            browser = playwright.chromium.launch(headless=False)
            context = browser.new_context(user_agent=random.choice(user_agents))
            context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            page = context.new_page()
            page.goto(
                "https://www.google.com.br/",
                timeout=60000,
                wait_until="domcontentloaded",
            )
            page.goto(
                f"https://www.marketwatch.com/investing/stock/{self.company_code}",
                timeout=60000,
                wait_until="domcontentloaded",
            )

            page.locator(".company__name").wait_for(timeout=10000, state="visible")
            company_name = page.locator(".company__name").first.inner_text()
            performance_data = page.locator(
                ".content__item.value.ignore-color"
            ).all_inner_texts()
            competitorsRows = page.locator(
                ".Competitors > table > tbody > tr"
            ).all_inner_texts()
            competitors = []
            for competitorRow in competitorsRows:
                competitorData = competitorRow.split("\t")
                competitors.append(
                    CompetitorSchema(
                        name=competitorData[0],
                        market_cap=MarketCapSchema(
                            currency=competitorData[2],
                            value=float(competitorData[1].strip("%")),
                        ),
                    )
                )
            stock_data = MarketWatchData(
                company_name=company_name,
                performance_data=PerformanceDataSchema(
                    five_days=float(performance_data[0].strip("%")),
                    one_month=float(performance_data[1].strip("%")),
                    three_months=float(performance_data[2].strip("%")),
                    year_to_date=float(performance_data[3].strip("%")),
                    one_year=float(performance_data[4].strip("%")),
                ),
                competitors=competitors,
            )
            browser.close()
            playwright.stop()
            if sys.platform.startswith("linux"):
                vdisplay.stop()
        except Exception as error:
            logger.error(error)
            browser.close()
            playwright.stop()
            if sys.platform.startswith("linux"):
                vdisplay.stop()
            raise NotFound(self.company_code)

        return stock_data
