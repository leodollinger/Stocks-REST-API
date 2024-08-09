from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.stock_model import *
from main import app
from shared.database import Base
from shared.dependencies import get_db

SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def populate_db():
    db = TestingSessionLocal()
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
            "request_data": datetime.strptime("2024-08-06", "%Y-%m-%d"),
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
    db.rollback()
    db.close()


populate_db()


def test_get_stock_data():
    response = client.get("/stock/AAPL")

    assert response.status_code == 200

    assert response.json() == {
        "status": "OK",
        "purchased_amount": 0,
        "purchased_status": "OK",
        "request_data": "2024-08-06",
        "company_code": "AAPL",
        "company_name": "Apple Inc.",
        "stock_values": {"open": 205.3, "high": 209.99, "low": 201.07, "close": 207.23},
        "performance_data": {
            "five_days": -5.52,
            "one_month": -9.94,
            "three_months": 14.82,
            "year_to_date": 8.98,
            "one_year": 17.75,
        },
        "competitors": [
            {
                "name": "Microsoft Corp.",
                "market_cap": {"currency": "$2.97T", "value": -0.3},
            }
        ],
    }


def test_get_non_existent_stock_data_error():
    response = client.get("/stock/xxxxx")

    assert response.status_code == 404

    assert response.json() == {"message": "xxxxx not found."}


def test_update_stock_amount():
    response = client.post("/stock/AAPL", json={"amount": 3})

    assert response.status_code == 201

    assert response.json() == {
        "message": "3 units of stock AAPL were added to your stock record"
    }


def test_update_stock_invalid_amount_error():
    response = client.post("/stock/AAPL", json={"amount": 3.5})

    assert response.status_code == 422


def test_update_non_existent_stock_amount_error():
    response = client.post("/stock/xxxxx", json={"amount": 1})

    assert response.status_code == 412

    assert response.json() == {"message": "Precondition failed, xxxxx is not valid."}
