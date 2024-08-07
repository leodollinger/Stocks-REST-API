from fastapi.testclient import TestClient
from datetime import datetime

from main import app

client = TestClient(app)


def test_get_stock_data():
    response = client.get("/stock/AAPL")

    assert response.status_code == 200

    assert response.json() == {
        "status": "",
        "purchased_amount": 0,
        "purchased_status": "",
        "request_data": datetime.now().strftime("%Y-%m-%dT00:00:00"),
        "company_code": "AAPL",
        "company_name": "",
        "stock_values": {"open": 0.0, "high": 0.0, "low": 0.0, "close": 0.0},
        "performance_data": {
            "five_days": 0.0,
            "one_month": 0.0,
            "three_months": 0.0,
            "year_to_date": 0.0,
            "one_year": 0.0,
        },
        "competitors": [{"name": ""}],
        "market_cap": {"currency": "", "value": 0.0},
    }


def test_update_stock_amount():
    response = client.post("/stock/AAPL", json={"amount": 3.53})

    assert response.status_code == 201

    assert response.json() == {
        "message": "3.53 units of stock AAPL were added to your stock record"
    }
