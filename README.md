
# Stocks-REST-API

This is a Stocks REST API using Python and FastAPI. This API retrieves stock data from the polygon API and performs a data scraping from the Marketwatch financial website. Once retrieved, it persists the data on a Postgres DB, making it possible to manage the purchased amount for each **searched** stock (it's necessary to search for the stock before adding a purchased amount to it)





## Running locally

Clone the project

```bash
  git clone https://github.com/leodollinger/Stocks-REST-API.git
```

Enter the project directory

```bash
  cd Stocks-REST-API
```

Build the Docker image

```bash
  docker build -t stocks .
```

Start the docker container

```bash
  docker run -p 8000:80 stocks
```


## Use/Example

The application exposes two endpoints.

### Get:

```http
curl -X 'GET' \
  'http://localhost:8000/stock/{stock_symbol}' \
  -H 'accept: application/json'
```
`stock_symbol (str):` company stock code. E.g.: "aapl" or "AAPL".

Returns a Json with stock data for the given symbol. There are two possible process with the get endpoint. If it is the first time searching for the stock, the application will search for it on the polygon API and perform a data scraping from the Marketwatch financial website and will then insert it on the database. If it is already on the database, the application gets the data from it.

Return:
```json
{
    "status":String,
    "purchased_amount":Integer,
    "purchased_status":String,
    "request_data":String,
    "company_code":String,
    "company_name":String,
    "stock_values":{
        "open":Float,
        "high":Float,
        "low":Float,
        "close":Float
    },
    "performance_data":{
        "five_days":Float,
        "one_month":Float,
        "three_months":Float,
        "year_to_date":Float,
        "one_year":Float
    },
    "competitors":[
        {
            "name":String,
            "market_cap":{
                "currency":String,
                "value":Float
            }
        }
    ]
}
```
### Post:

```http
curl -X 'POST' \
  'http://localhost:8000/stock/{stock_symbol}' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "amount": {amount}
}'
```
`stock_symbol (str):` company stock code. E.g.: "aapl" or "AAPL".

`amount (int):` desired amount to add into purchased amount.

Update the stock entity with the purchased amount based on received argument: “amount” (of type Integer). Before updating the purchased amount for a certain stock, it is necessary to search for it on the get endpoint.
Returns a Json with the message `“{amount} units of stock {stock_symbol} were added to your stock record”`.


Return:
```json
{
    "message":String
}
```

## Main Packages
* FastApi: FastAPI is a modern, fast (high-performance), web framework for building APIs with Python based on standard Python type hints.

* SQLAlchemy: SQLAlchemy is the Python SQL toolkit and Object Relational Mapper that gives application developers the full power and flexibility of SQL. 

* playwright: Playwright is a Python library to automate Chromium, Firefox and WebKit browsers with a single API.

* pydantic: Data validation using Python type hints. Fast and extensible, Pydantic plays nicely with your linters/IDE/brain. Define how data should be in pure, canonical Python 3.8+; validate it with Pydantic.

* pytest: The pytest framework makes it easy to write small tests, yet scales to support complex functional testing for applications and libraries

* alembic: Alembic is a database migrations tool written by the author of SQLAlchemy.

* uvicorn: Uvicorn is an ASGI web server implementation for Python

* xvfbwrapper: Xvfb (X virtual framebuffer) is a display server implementing the X11 display server protocol. It runs in memory and does not require a physical display. Only a network layer is necessary.


## Running testes

It is necessary to install all the project dependencies and then run the following command:

```bash
  pytest
```
