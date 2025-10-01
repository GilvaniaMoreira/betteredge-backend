from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from enum import Enum
from .client import ClientSummary


class TransactionType(str, Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"


class TransactionCreate(BaseModel):
    client_id: int
    type: TransactionType
    amount: float
    date: datetime
    note: Optional[str] = None

    class Config:
        use_enum_values = True


class TransactionResponse(BaseModel):
    id: int
    client_id: int
    type: TransactionType
    amount: float
    date: datetime
    note: Optional[str]
    created_at: datetime
    client: Optional[ClientSummary] = None

    class Config:
        from_attributes = True
        use_enum_values = True


class TransactionList(BaseModel):
    items: List[TransactionResponse]
    total: int
    page: int
    size: int
    pages: int


class TransactionFilter(BaseModel):
    client_id: Optional[int] = None
    type: Optional[TransactionType] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class CaptationSummary(BaseModel):
    total_deposits: float
    total_withdrawals: float
    net_captation: float
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class ClientCaptationSummary(BaseModel):
    client_id: int
    client_name: str
    client_email: str
    total_deposits: float
    total_withdrawals: float
    net_captation: float


class CaptationReport(BaseModel):
    summary: CaptationSummary
    clients: List[ClientCaptationSummary]

