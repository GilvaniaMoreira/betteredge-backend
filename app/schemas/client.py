from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List


class ClientSummary(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True


class ClientCreate(BaseModel):
    name: str
    email: EmailStr
    is_active: bool = True


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class ClientResponse(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ClientList(BaseModel):
    items: List[ClientResponse]
    total: int
    page: int
    size: int
    pages: int



