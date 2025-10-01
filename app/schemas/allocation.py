from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional, List


class ClientSummary(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True


class AssetSummary(BaseModel):
    id: int
    ticker: str
    name: str

    class Config:
        from_attributes = True


class AllocationCreate(BaseModel):
    client_id: int
    asset_id: int
    quantity: float
    buy_price: float
    buy_date: datetime

    @field_validator('buy_date', mode='before')
    @classmethod
    def parse_buy_date(cls, v):
        if isinstance(v, str):
            # Parse ISO string and remove timezone info
            dt = datetime.fromisoformat(v.replace('Z', '+00:00'))
            return dt.replace(tzinfo=None)
        return v


class AllocationResponse(BaseModel):
    id: int
    client_id: int
    asset_id: int
    quantity: float
    buy_price: float
    buy_date: datetime
    created_at: datetime
    client: Optional[ClientSummary] = None
    asset: Optional[AssetSummary] = None

    class Config:
        from_attributes = True


class AllocationList(BaseModel):
    items: List[AllocationResponse]
    total: int
    page: int
    size: int
    pages: int


class AllocationCreateByTicker(BaseModel):
    client_id: int
    ticker: str
    quantity: float
    buy_price: float
    buy_date: datetime

