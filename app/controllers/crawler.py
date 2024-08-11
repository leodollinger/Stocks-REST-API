from playwright.sync_api import sync_playwright
from functools import cache
from app.schemas.stock_schema import (
    CompetitorSchema,
    MarketCapSchema,
    MarketWatchData,
    PerformanceDataSchema,
)
import random
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@cache
def get_web_data(stock_symbol: str) -> MarketWatchData:
    """Scraps MarketWatch website and gets data on given stock

    Args:
        stock_symbol (str): company stock code. E.g.: "aapl" or "AAPL"

    Returns:
        MarketWatchData: pydantic schema with marketwatch website data. If process fails, return empty version of schema
    """
    try:
        logger.debug(f"starting crawler for stock {stock_symbol}")
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
            "https://www.google.com.br/", timeout=60000, wait_until="domcontentloaded"
        )
        page.goto(
            f"https://www.marketwatch.com/investing/stock/{stock_symbol}",
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
    except Exception as error:
        logger.error(error)
        stock_data = MarketWatchData(
            company_name="",
            performance_data=PerformanceDataSchema(
                five_days=0.0,
                one_month=0.0,
                three_months=0.0,
                year_to_date=0.0,
                one_year=0.0,
            ),
            competitors=[],
        )
        browser.close()
        playwright.stop()

    return stock_data
