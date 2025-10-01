from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.allocation import AllocationCreate, AllocationResponse, AllocationList, AllocationCreateByTicker
from app.services.allocation_service import AllocationService
from app.services.client_service import ClientService
from app.services.asset_service import AssetService
from app.models.user import User
from app.api.dependencies import get_current_user
from typing import Optional

router = APIRouter(prefix="/allocations", tags=["allocations"])


@router.post("/", response_model=AllocationResponse)
async def create_allocation(
    allocation_data: AllocationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new allocation"""
    allocation_service = AllocationService(db)
    client_service = ClientService(db)
    asset_service = AssetService(db)
    
    # Verify client exists
    client = await client_service.get_client(allocation_data.client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    # Verify asset exists
    asset = await asset_service.get_asset(allocation_data.asset_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )
    
    allocation = await allocation_service.create_allocation(allocation_data)
    return allocation


@router.get("/", response_model=AllocationList)
async def get_allocations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    client_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get allocations with pagination and optional client filter"""
    allocation_service = AllocationService(db)
    allocations, total = await allocation_service.get_allocations(skip, limit, client_id)
    
    pages = (total + limit - 1) // limit
    
    return AllocationList(
        items=allocations,
        total=total,
        page=skip // limit + 1,
        size=limit,
        pages=pages
    )


@router.get("/{allocation_id}", response_model=AllocationResponse)
async def get_allocation(
    allocation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get allocation by ID"""
    allocation_service = AllocationService(db)
    allocation = await allocation_service.get_allocation(allocation_id)
    
    if not allocation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Allocation not found"
        )
    
    return allocation


@router.put("/{allocation_id}", response_model=AllocationResponse)
async def update_allocation(
    allocation_id: int,
    allocation_data: AllocationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing allocation"""
    allocation_service = AllocationService(db)
    client_service = ClientService(db)
    asset_service = AssetService(db)
    
    # Verify allocation exists
    existing_allocation = await allocation_service.get_allocation(allocation_id)
    if not existing_allocation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Allocation not found"
        )
    
    # Verify client exists
    client = await client_service.get_client(allocation_data.client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    # Verify asset exists
    asset = await asset_service.get_asset(allocation_data.asset_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )
    
    allocation = await allocation_service.update_allocation(allocation_id, allocation_data)
    return allocation


@router.delete("/{allocation_id}")
async def delete_allocation(
    allocation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an allocation"""
    allocation_service = AllocationService(db)
    
    # Verify allocation exists
    existing_allocation = await allocation_service.get_allocation(allocation_id)
    if not existing_allocation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Allocation not found"
        )
    
    await allocation_service.delete_allocation(allocation_id)
    return {"message": "Allocation deleted successfully"}


@router.get("/client/{client_id}", response_model=list[AllocationResponse])
async def get_client_allocations(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all allocations for a specific client"""
    allocation_service = AllocationService(db)
    client_service = ClientService(db)
    
    # Verify client exists
    client = await client_service.get_client(client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    allocations = await allocation_service.get_client_allocations(client_id)
    return allocations


@router.get("/stats/total-value")
async def get_total_allocation_value(
    client_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get total allocation value for all clients or specific client"""
    allocation_service = AllocationService(db)
    
    if client_id:
        # Verify client exists
        client_service = ClientService(db)
        client = await client_service.get_client(client_id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )
    
    total_value = await allocation_service.get_total_allocation_value(client_id)
    
    return {
        "total_value": total_value,
        "client_id": client_id
    }

