from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from shared.database import Base


class StockValues(Base):
    __tablename__ = "stock_values_table"

    id = Column(Integer, primary_key=True, autoincrement=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)


class PerformanceData(Base):
    __tablename__ = "performance_data_table"

    id = Column(Integer, primary_key=True, autoincrement=True)
    five_days = Column(Float)
    one_month = Column(Float)
    three_months = Column(Float)
    year_to_date = Column(Float)
    one_year = Column(Float)


class MarketCap(Base):
    __tablename__ = "market_cap_table"

    id = Column(Integer, primary_key=True, autoincrement=True)
    currency = Column(String(15))
    value = Column(Float)


class Stock(Base):
    __tablename__ = "stock_table"

    id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(String(15))
    purchased_amount = Column(Integer)
    purchased_status = Column(String(15))
    request_data = Column(Date)
    company_code = Column(String(20), unique=True)
    company_name = Column(String(150))

    stock_values_id = Column(
        Integer, ForeignKey("stock_values_table.id"), nullable=False, index=True
    )
    performance_data_id = Column(
        Integer, ForeignKey("performance_data_table.id"), nullable=False, index=True
    )

    stock_values = relationship("StockValues")
    performance_data = relationship("PerformanceData")


class Competitor(Base):
    __tablename__ = "competitor_table"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150))
    stock_id = Column(Integer, ForeignKey("stock_table.id"), nullable=False, index=True)
    market_cap_id = Column(
        Integer, ForeignKey("market_cap_table.id"), nullable=False, index=True
    )

    stock = relationship("Stock")
    market_cap = relationship("MarketCap")
