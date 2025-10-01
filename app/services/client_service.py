from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientUpdate
from typing import Optional, Tuple


class ClientService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_client(self, client_data: ClientCreate) -> Client:
        """Create a new client"""
        db_client = Client(**client_data.dict())
        self.db.add(db_client)
        await self.db.commit()
        await self.db.refresh(db_client)
        return db_client

    async def get_client(self, client_id: int) -> Client | None:
        """Get client by ID"""
        result = await self.db.execute(
            select(Client).where(Client.id == client_id)
        )
        return result.scalar_one_or_none()

    async def get_client_by_email(self, email: str) -> Client | None:
        """Get client by email"""
        result = await self.db.execute(
            select(Client).where(Client.email == email)
        )
        return result.scalar_one_or_none()

    async def get_clients(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        search: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[list[Client], int]:
        """Get clients with pagination, search and filter"""
        query = select(Client)
        count_query = select(func.count(Client.id))

        # Apply filters
        filters = []
        if search:
            search_filter = or_(
                Client.name.ilike(f"%{search}%"),
                Client.email.ilike(f"%{search}%")
            )
            filters.append(search_filter)
        
        if is_active is not None:
            filters.append(Client.is_active == is_active)

        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        clients = result.scalars().all()
        
        return list(clients), total

    async def update_client(self, client_id: int, client_data: ClientUpdate) -> Client | None:
        """Update client"""
        client = await self.get_client(client_id)
        if not client:
            return None

        update_data = client_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(client, field, value)

        await self.db.commit()
        await self.db.refresh(client)
        return client

    async def delete_client(self, client_id: int) -> bool:
        """Delete client (soft delete by setting is_active=False)"""
        client = await self.get_client(client_id)
        if not client:
            return False

        client.is_active = False
        await self.db.commit()
        return True
