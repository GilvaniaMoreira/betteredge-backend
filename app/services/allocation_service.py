from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from app.models.allocation import Allocation
from app.models.client import Client
from app.models.asset import Asset
from app.schemas.allocation import AllocationCreate
from app.services.asset_service import AssetService
from typing import Optional, Tuple
from datetime import datetime


class AllocationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_allocation(self, allocation_data: AllocationCreate) -> Allocation:
        """Create a new allocation"""
        db_allocation = Allocation(**allocation_data.dict())
        self.db.add(db_allocation)
        await self.db.commit()
        await self.db.refresh(db_allocation)
        
        # Load relationships
        result = await self.db.execute(
            select(Allocation)
            .options(selectinload(Allocation.client), selectinload(Allocation.asset))
            .where(Allocation.id == db_allocation.id)
        )
        return result.scalar_one()

    async def get_allocation(self, allocation_id: int) -> Allocation | None:
        """Get allocation by ID"""
        result = await self.db.execute(
            select(Allocation)
            .options(selectinload(Allocation.client), selectinload(Allocation.asset))
            .where(Allocation.id == allocation_id)
        )
        return result.scalar_one_or_none()

    async def get_allocations(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        client_id: Optional[int] = None
    ) -> Tuple[list[Allocation], int]:
        """Get allocations with pagination and optional client filter"""
        query = select(Allocation).options(
            selectinload(Allocation.client), 
            selectinload(Allocation.asset)
        )
        count_query = select(func.count(Allocation.id))

        # Apply client filter
        if client_id:
            query = query.where(Allocation.client_id == client_id)
            count_query = count_query.where(Allocation.client_id == client_id)

        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        allocations = result.scalars().all()
        
        return list(allocations), total

    async def get_client_allocations(self, client_id: int) -> list[Allocation]:
        """Get all allocations for a specific client"""
        result = await self.db.execute(
            select(Allocation)
            .options(selectinload(Allocation.asset))
            .where(Allocation.client_id == client_id)
        )
        return list(result.scalars().all())

    async def get_total_allocation_value(self, client_id: Optional[int] = None) -> float:
        """Get total allocation value for all clients or specific client"""
        query = select(func.sum(Allocation.quantity * Allocation.buy_price))
        
        if client_id:
            query = query.where(Allocation.client_id == client_id)
        
        result = await self.db.execute(query)
        total = result.scalar()
        return total or 0.0

    async def update_allocation(self, allocation_id: int, allocation_data: AllocationCreate) -> Allocation:
        """Update an existing allocation"""
        # Get existing allocation
        existing_allocation = await self.get_allocation(allocation_id)
        if not existing_allocation:
            raise ValueError("Allocation not found")
        
        # Update allocation fields
        existing_allocation.client_id = allocation_data.client_id
        existing_allocation.asset_id = allocation_data.asset_id
        existing_allocation.quantity = allocation_data.quantity
        existing_allocation.buy_price = allocation_data.buy_price
        existing_allocation.buy_date = allocation_data.buy_date
        
        # Save changes
        self.db.add(existing_allocation)
        await self.db.commit()
        await self.db.refresh(existing_allocation)
        
        return existing_allocation

    async def delete_allocation(self, allocation_id: int) -> None:
        """Delete an allocation"""
        # Get existing allocation
        existing_allocation = await self.get_allocation(allocation_id)
        if not existing_allocation:
            raise ValueError("Allocation not found")
        
        # Delete allocation
        await self.db.delete(existing_allocation)
        await self.db.commit()

