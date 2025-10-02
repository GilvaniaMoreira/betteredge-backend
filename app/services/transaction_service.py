from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, case, literal, text
from sqlalchemy.orm import selectinload
from app.models.transaction import Transaction, TransactionType
from app.models.client import Client
from app.schemas.transaction import TransactionCreate, TransactionFilter, CaptationSummary, ClientCaptationSummary, CaptationReport
from typing import Optional, Tuple, List
from datetime import datetime


class TransactionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_transaction(self, transaction_data: TransactionCreate) -> Transaction:
        db_transaction = Transaction(**transaction_data.dict())
        self.db.add(db_transaction)
        await self.db.commit()
        await self.db.refresh(db_transaction)
        
        await self.db.refresh(
            db_transaction, 
            attribute_names=["client"]
        )
        return db_transaction

    async def get_transaction(self, transaction_id: int) -> Transaction | None:
        result = await self.db.execute(
            select(Transaction)
            .options(selectinload(Transaction.client))
            .where(Transaction.id == transaction_id)
        )
        return result.scalar_one_or_none()

    async def get_transactions(
        self, 
        page: int = 1, 
        size: int = 10, 
        filters: Optional[TransactionFilter] = None
    ) -> Tuple[List[Transaction], int]:
        query = select(Transaction).options(selectinload(Transaction.client))
        
        if filters:
            if filters.client_id:
                query = query.where(Transaction.client_id == filters.client_id)
            if filters.type:
                query = query.where(Transaction.type == filters.type)
            if filters.start_date:
                query = query.where(Transaction.date >= filters.start_date)
            if filters.end_date:
                query = query.where(Transaction.date <= filters.end_date)
        
        # Get total count
        count_query = select(func.count(Transaction.id))
        if filters:
            if filters.client_id:
                count_query = count_query.where(Transaction.client_id == filters.client_id)
            if filters.type:
                count_query = count_query.where(Transaction.type == filters.type)
            if filters.start_date:
                count_query = count_query.where(Transaction.date >= filters.start_date)
            if filters.end_date:
                count_query = count_query.where(Transaction.date <= filters.end_date)
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination and ordering
        query = query.order_by(desc(Transaction.date)).offset((page - 1) * size).limit(size)
        
        result = await self.db.execute(query)
        transactions = result.scalars().all()
        
        return transactions, total

    async def update_transaction(self, transaction_id: int, transaction_data: TransactionCreate) -> Transaction | None:
        transaction = await self.get_transaction(transaction_id)
        if not transaction:
            return None
        
        for field, value in transaction_data.dict().items():
            setattr(transaction, field, value)
        
        await self.db.commit()
        await self.db.refresh(transaction)
        return transaction

    async def delete_transaction(self, transaction_id: int) -> bool:
        transaction = await self.get_transaction(transaction_id)
        if not transaction:
            return False
        
        await self.db.delete(transaction)
        await self.db.commit()
        return True

    async def get_captation_report(
        self, 
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None,
        client_id: Optional[int] = None
    ) -> CaptationReport:
        
        base_query = select(Transaction)
        if start_date:
            base_query = base_query.where(Transaction.date >= start_date)
        if end_date:
            base_query = base_query.where(Transaction.date <= end_date)
        if client_id:
            base_query = base_query.where(Transaction.client_id == client_id)
        
        # Get total deposits
        deposits_query = select(func.sum(Transaction.amount)).where(
            Transaction.type == TransactionType.DEPOSIT
        )
        
        # Get total withdrawals
        withdrawals_query = select(func.sum(Transaction.amount)).where(
            Transaction.type == TransactionType.WITHDRAWAL
        )
        
        # Apply date filters to both queries
        if start_date:
            deposits_query = deposits_query.where(Transaction.date >= start_date)
            withdrawals_query = withdrawals_query.where(Transaction.date >= start_date)
        if end_date:
            deposits_query = deposits_query.where(Transaction.date <= end_date)
            withdrawals_query = withdrawals_query.where(Transaction.date <= end_date)
        if client_id:
            deposits_query = deposits_query.where(Transaction.client_id == client_id)
            withdrawals_query = withdrawals_query.where(Transaction.client_id == client_id)
        
        # Execute queries
        deposits_result = await self.db.execute(deposits_query)
        withdrawals_result = await self.db.execute(withdrawals_query)
        
        total_deposits = deposits_result.scalar() or 0
        total_withdrawals = withdrawals_result.scalar() or 0
        
        net_captation = total_deposits - total_withdrawals
        
        summary = CaptationSummary(
            total_deposits=total_deposits,
            total_withdrawals=total_withdrawals,
            net_captation=net_captation,
            period_start=start_date,
            period_end=end_date
        )
        
        # Get per-client breakdown - we'll do this with separate queries for simplicity
        clients_query = select(Client.id, Client.name, Client.email).distinct()
        
        if client_id:
            clients_query = clients_query.where(Client.id == client_id)
        
        clients_result = await self.db.execute(clients_query)
        clients = clients_result.all()
        
        client_summaries = []
        for client in clients:
            # Get deposits for this client
            client_deposits_query = select(func.sum(Transaction.amount)).where(
                and_(
                    Transaction.client_id == client.id,
                    Transaction.type == TransactionType.DEPOSIT
                )
            )
            
            # Get withdrawals for this client
            client_withdrawals_query = select(func.sum(Transaction.amount)).where(
                and_(
                    Transaction.client_id == client.id,
                    Transaction.type == TransactionType.WITHDRAWAL
                )
            )
            
            # Apply date filters
            if start_date:
                client_deposits_query = client_deposits_query.where(Transaction.date >= start_date)
                client_withdrawals_query = client_withdrawals_query.where(Transaction.date >= start_date)
            if end_date:
                client_deposits_query = client_deposits_query.where(Transaction.date <= end_date)
                client_withdrawals_query = client_withdrawals_query.where(Transaction.date <= end_date)
            
            deposits_result = await self.db.execute(client_deposits_query)
            withdrawals_result = await self.db.execute(client_withdrawals_query)
            
            client_deposits = deposits_result.scalar() or 0
            client_withdrawals = withdrawals_result.scalar() or 0
            client_net = client_deposits - client_withdrawals
            
            client_summaries.append(ClientCaptationSummary(
                client_id=client.id,
                client_name=client.name,
                client_email=client.email,
                total_deposits=float(client_deposits),
                total_withdrawals=float(client_withdrawals),
                net_captation=float(client_net)
            ))
        
        return CaptationReport(summary=summary, clients=client_summaries)

    async def get_client_transactions(
        self, 
        client_id: int, 
        page: int = 1, 
        size: int = 10,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Tuple[List[Transaction], int]:
        filters = TransactionFilter(
            client_id=client_id,
            start_date=start_date,
            end_date=end_date
        )
        return await self.get_transactions(page, size, filters)