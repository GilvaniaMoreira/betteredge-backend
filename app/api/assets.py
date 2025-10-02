from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.asset import AssetCreate, AssetResponse, AssetList, AssetSearchResponse, AssetSearchSimpleResponse
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


@router.get("/yahoo/search", response_model=list[AssetSearchSimpleResponse])
async def search_yahoo_assets_by_name(
    query: str = Query(..., min_length=1, description="Search query for asset name or ticker"),
    limit: int = Query(10, ge=1, le=20, description="Maximum number of results to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search Yahoo Finance assets by name or ticker (simplified results for autocomplete)"""
    asset_service = AssetService(db)
    search_results = await asset_service.search_yahoo_assets_by_name(query, limit)

    if not search_results:
        return []

    return search_results


@router.get("/yahoo/details/{ticker}", response_model=AssetSearchResponse)
async def get_yahoo_asset_details(
    ticker: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed information for a specific ticker from Yahoo Finance"""
    asset_service = AssetService(db)
    asset_details = await asset_service.get_yahoo_asset_details(ticker)

    if not asset_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found or unable to fetch details"
        )

    return asset_details



