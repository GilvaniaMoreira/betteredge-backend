from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.transaction import (
    TransactionCreate, TransactionResponse, TransactionList, TransactionFilter,
    CaptationReport, TransactionType
)
from app.services.transaction_service import TransactionService
from app.services.client_service import ClientService
from app.models.user import User
from app.api.dependencies import get_current_user
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/", response_model=TransactionResponse)
async def create_transaction(
    transaction_data: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new transaction (deposit or withdrawal)"""
    transaction_service = TransactionService(db)
    client_service = ClientService(db)
    
    # Verify client exists
    client = await client_service.get_client(transaction_data.client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    # Validate amount
    if transaction_data.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be greater than 0"
        )
    
    transaction = await transaction_service.create_transaction(transaction_data)
    return transaction


@router.get("/", response_model=TransactionList)
async def get_transactions(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    client_id: Optional[int] = Query(None),
    type: Optional[TransactionType] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get transactions with optional filtering"""
    transaction_service = TransactionService(db)
    
    filters = TransactionFilter(
        client_id=client_id,
        type=type,
        start_date=start_date,
        end_date=end_date
    )
    
    transactions, total = await transaction_service.get_transactions(page, size, filters)
    
    return TransactionList(
        items=transactions,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific transaction by ID"""
    transaction_service = TransactionService(db)
    transaction = await transaction_service.get_transaction(transaction_id)
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    return transaction


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: int,
    transaction_data: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a transaction"""
    transaction_service = TransactionService(db)
    client_service = ClientService(db)
    
    # Verify client exists
    client = await client_service.get_client(transaction_data.client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    # Validate amount
    if transaction_data.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be greater than 0"
        )
    
    transaction = await transaction_service.update_transaction(transaction_id, transaction_data)
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    return transaction


@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a transaction"""
    transaction_service = TransactionService(db)
    success = await transaction_service.delete_transaction(transaction_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    return {"message": "Transaction deleted successfully"}


@router.get("/client/{client_id}", response_model=TransactionList)
async def get_client_transactions(
    client_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get transactions for a specific client"""
    transaction_service = TransactionService(db)
    client_service = ClientService(db)
    
    # Verify client exists
    client = await client_service.get_client(client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    transactions, total = await transaction_service.get_client_transactions(
        client_id, page, size, start_date, end_date
    )
    
    return TransactionList(
        items=transactions,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )


@router.get("/reports/captation", response_model=CaptationReport)
async def get_captation_report(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    client_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get captation report with summary and per-client breakdown"""
    transaction_service = TransactionService(db)
    
    # If client_id is provided, verify client exists
    if client_id:
        client_service = ClientService(db)
        client = await client_service.get_client(client_id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )
    
    report = await transaction_service.get_captation_report(start_date, end_date, client_id)
    return report