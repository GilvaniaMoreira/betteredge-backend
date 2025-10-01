from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.asset import AssetCreate, AssetResponse, AssetList, AssetSearchRequest, AssetSearchResponse
from app.services.asset_service import AssetService
from app.models.user import User
from app.api.dependencies import get_current_user
from typing import Optional

router = APIRouter(prefix="/assets", tags=["assets"])


@router.post("/", response_model=AssetResponse)
async def create_asset(
    asset_data: AssetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new asset"""
    asset_service = AssetService(db)
    
    # Check if asset with ticker already exists
    existing_asset = await asset_service.get_asset_by_ticker(asset_data.ticker)
    if existing_asset:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Asset with this ticker already exists"
        )
    
    asset = await asset_service.create_asset(asset_data)
    return asset


@router.get("/", response_model=AssetList)
async def get_assets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get assets with pagination and search"""
    asset_service = AssetService(db)
    assets, total = await asset_service.get_assets(skip, limit, search)
    
    pages = (total + limit - 1) // limit
    
    return AssetList(
        items=assets,
        total=total,
        page=skip // limit + 1,
        size=limit,
        pages=pages
    )


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get asset by ID"""
    asset_service = AssetService(db)
    asset = await asset_service.get_asset(asset_id)
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )
    
    return asset


@router.post("/search", response_model=AssetSearchResponse)
async def search_asset_from_yahoo(
    search_request: AssetSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search and fetch asset data from Yahoo Finance without saving"""
    asset_service = AssetService(db)
    yahoo_data = await asset_service.fetch_asset_from_yahoo(search_request.ticker)
    
    if not yahoo_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not fetch asset data from Yahoo Finance"
        )
    
    return yahoo_data


@router.put("/{asset_id}/update-price", response_model=AssetResponse)
async def update_asset_price(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update asset price from Yahoo Finance"""
    asset_service = AssetService(db)
    asset = await asset_service.get_asset(asset_id)
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )
    
    # Fetch updated data from Yahoo Finance
    yahoo_data = await asset_service.fetch_asset_from_yahoo(asset.ticker)
    if not yahoo_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not fetch updated data from Yahoo Finance"
        )
    
    # Update asset with new data
    updated_asset = await asset_service.update_asset_from_yahoo(asset_id, yahoo_data)
    return updated_asset

