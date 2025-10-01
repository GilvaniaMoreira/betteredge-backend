from sqlalchemy import Column, Integer, String, DateTime, Float, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    exchange = Column(String, nullable=True)
    currency = Column(String, nullable=True)
    current_price = Column(Float, nullable=True)
    sector = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    market_cap = Column(BigInteger, nullable=True)
    volume = Column(BigInteger, nullable=True)
    pe_ratio = Column(Float, nullable=True)
    dividend_yield = Column(Float, nullable=True)
    last_updated = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relacionamentos
    allocations = relationship("Allocation", back_populates="asset")
