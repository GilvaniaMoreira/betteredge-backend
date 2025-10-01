from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class AssetCreate(BaseModel):
    ticker: str
    name: str
    exchange: Optional[str] = None
    currency: Optional[str] = None
    current_price: Optional[float] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[int] = None
    volume: Optional[int] = None
    pe_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    last_updated: Optional[datetime] = None


class AssetResponse(BaseModel):
    id: int
    ticker: str
    name: str
    exchange: Optional[str]
    currency: Optional[str]
    current_price: Optional[float]
    sector: Optional[str]
    industry: Optional[str]
    market_cap: Optional[int]
    volume: Optional[int]
    pe_ratio: Optional[float]
    dividend_yield: Optional[float]
    last_updated: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class AssetList(BaseModel):
    items: List[AssetResponse]
    total: int
    page: int
    size: int
    pages: int


class AssetSearchRequest(BaseModel):
    ticker: str


class AssetSearchResponse(BaseModel):
    ticker: str
    name: str
    exchange: Optional[str]
    currency: Optional[str]
    current_price: Optional[float]
    sector: Optional[str]
    industry: Optional[str]
    market_cap: Optional[int]
    volume: Optional[int]
    pe_ratio: Optional[float]
    dividend_yield: Optional[float]
    last_updated: Optional[datetime]

    class Config:
        from_attributes = True

