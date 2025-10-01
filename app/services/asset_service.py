from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from app.models.asset import Asset
from app.schemas.asset import AssetCreate
from typing import Optional, Tuple, Dict, Any
import asyncio
import yfinance as yf
from datetime import datetime


class AssetService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_asset(self, asset_data: AssetCreate) -> Asset:
        """Create a new asset"""
        db_asset = Asset(**asset_data.dict())
        self.db.add(db_asset)
        await self.db.commit()
        await self.db.refresh(db_asset)
        return db_asset

    async def get_asset(self, asset_id: int) -> Asset | None:
        """Get asset by ID"""
        result = await self.db.execute(
            select(Asset).where(Asset.id == asset_id)
        )
        return result.scalar_one_or_none()

    async def get_asset_by_ticker(self, ticker: str) -> Asset | None:
        """Get asset by ticker"""
        result = await self.db.execute(
            select(Asset).where(Asset.ticker == ticker)
        )
        return result.scalar_one_or_none()

    async def get_assets(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        search: Optional[str] = None
    ) -> Tuple[list[Asset], int]:
        """Get assets with pagination and search"""
        query = select(Asset)
        count_query = select(func.count(Asset.id))

        # Apply search filter
        if search:
            search_filter = or_(
                Asset.ticker.ilike(f"%{search}%"),
                Asset.name.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        assets = result.scalars().all()
        
        return list(assets), total

    async def fetch_asset_from_yahoo(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Fetch asset data from Yahoo Finance API using yfinance"""
        try:
            # Run yfinance in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            def fetch_ticker_data():
                ticker_obj = yf.Ticker(ticker)
                info = ticker_obj.info
                hist = ticker_obj.history(period="1d")
                return info, hist
            
            info, hist = await loop.run_in_executor(None, fetch_ticker_data)
            
            # Check if we got valid data
            if not info or len(info) == 0:
                print(f"No data received for ticker: {ticker}")
                return None
            
            # Get current price
            current_price = None
            if not hist.empty and 'Close' in hist.columns:
                close_prices = hist['Close'].dropna()
                if not close_prices.empty:
                    current_price = close_prices.iloc[-1]
            
            return {
                "ticker": ticker.upper(),
                "name": info.get("longName", ticker),
                "exchange": info.get("exchange", ""),
                "currency": info.get("currency", "USD"),
                "current_price": float(current_price) if current_price is not None else None,
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "market_cap": info.get("marketCap"),
                "volume": info.get("volume"),
                "pe_ratio": info.get("trailingPE"),
                "dividend_yield": info.get("dividendYield"),
                "last_updated": datetime.utcnow()
            }
        except Exception as e:
            print(f"Error fetching asset from Yahoo Finance for {ticker}: {e}")
            return None

    async def update_asset_from_yahoo(self, asset_id: int, yahoo_data: Dict[str, Any]) -> Asset | None:
        """Update existing asset with Yahoo Finance data"""
        asset = await self.get_asset(asset_id)
        if not asset:
            return None

        # Update asset fields
        for field, value in yahoo_data.items():
            if hasattr(asset, field) and value is not None:
                setattr(asset, field, value)

        await self.db.commit()
        await self.db.refresh(asset)
        return asset

