#!/usr/bin/env python3
"""
Simple database seeding script for BetterEdge Backend
Run with: python seed.py
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import AsyncSessionLocal
from app.services.auth_service import AuthService
from app.services.client_service import ClientService
from app.services.asset_service import AssetService
from app.schemas.user import UserCreate
from app.schemas.client import ClientCreate
from app.schemas.asset import AssetCreate
from datetime import datetime


# Popular tickers for seeding
POPULAR_TICKERS = [
    # US Stocks
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX", "AMD", "INTC",
    "JPM", "BAC", "WMT", "PG", "JNJ", "V", "MA", "DIS", "PYPL", "ADBE",
    
    # Brazilian Stocks (B3) - Using .SA suffix for Yahoo Finance
    "VALE3.SA", "PETR4.SA", "ITUB4.SA", "BBDC4.SA", "ABEV3.SA", "MGLU3.SA", "WEGE3.SA", "RENT3.SA", "SUZB3.SA", "B3SA3.SA",
    "LREN3.SA", "JBSS3.SA", "RADL3.SA", "PETR3.SA", "BBAS3.SA", "BOVA11.SA", "SMAL11.SA", "IVVB11.SA",
    
    # ETFs
    "SPY", "QQQ", "VTI", "VOO", "ARKK", "TQQQ", "SOXL",
    
    # Crypto (if available)
    "BTC-USD", "ETH-USD", "ADA-USD"
]


async def check_database_connection():
    """Check if database is accessible"""
    try:
        async with AsyncSessionLocal() as db_session:
            # Just try to create a session - this will test the connection
            print("✅ Database connection successful")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


async def create_admin_user(db_session):
    """Create admin user"""
    auth_service = AuthService(db_session)
    
    admin_email = "admin@betteredge.com"
    
    # Check if admin already exists
    existing_admin = await auth_service.get_user_by_email(admin_email)
    if existing_admin:
        print(f"✅ Admin user already exists: {admin_email}")
        return existing_admin
    
    # Create admin user
    admin_data = UserCreate(
        email=admin_email,
        password="admin123"  # Change this in production!
    )
    
    admin_user = await auth_service.create_user(admin_data)
    print(f"✅ Created admin user: {admin_email} (ID: {admin_user.id})")
    print(f"   Password: admin123")
    return admin_user


async def create_sample_clients(db_session):
    """Create sample clients"""
    client_service = ClientService(db_session)
    
    sample_clients = [
        {"name": "João Silva", "email": "joao.silva@email.com"},
        {"name": "Maria Santos", "email": "maria.santos@email.com"},
        {"name": "Pedro Oliveira", "email": "pedro.oliveira@email.com"},
        {"name": "Ana Costa", "email": "ana.costa@email.com"},
        {"name": "Carlos Ferreira", "email": "carlos.ferreira@email.com"},
        {"name": "Lucia Rodrigues", "email": "lucia.rodrigues@email.com"},
        {"name": "Roberto Alves", "email": "roberto.alves@email.com"},
        {"name": "Fernanda Lima", "email": "fernanda.lima@email.com"},
    ]
    
    created_clients = []
    skipped_clients = 0
    
    for client_data in sample_clients:
        # Check if client already exists
        existing_client = await client_service.get_client_by_email(client_data["email"])
        if existing_client:
            print(f"✅ Client already exists: {client_data['name']} ({client_data['email']})")
            created_clients.append(existing_client)
            skipped_clients += 1
            continue
        
        # Create client
        client_create = ClientCreate(**client_data)
        client = await client_service.create_client(client_create)
        created_clients.append(client)
        print(f"✅ Created client: {client.name} ({client.email})")
    
    return created_clients, skipped_clients


async def fetch_and_create_assets(db_session, tickers):
    """Fetch assets from Yahoo Finance and create them in database"""
    asset_service = AssetService(db_session)
    
    created_assets = []
    skipped_assets = 0
    failed_tickers = []
    
    print(f"🔄 Processing {len(tickers)} assets from Yahoo Finance...")
    
    for i, ticker in enumerate(tickers, 1):
        print(f"📈 [{i}/{len(tickers)}] Processing {ticker}...")
        
        # Check if asset already exists
        existing_asset = await asset_service.get_asset_by_ticker(ticker)
        if existing_asset:
            print(f"   ✅ Asset already exists: {ticker}")
            created_assets.append(existing_asset)
            skipped_assets += 1
            continue
        
        # Fetch from Yahoo Finance
        yahoo_data = await asset_service.fetch_asset_from_yahoo(ticker)
        
        if not yahoo_data:
            print(f"   ❌ Failed to fetch data for {ticker}")
            failed_tickers.append(ticker)
            continue
        
        # Create asset
        try:
            asset_data = AssetCreate(
                ticker=yahoo_data["ticker"],
                name=yahoo_data["name"],
                exchange=yahoo_data.get("exchange", ""),
                currency=yahoo_data.get("currency", "USD"),
                current_price=yahoo_data.get("current_price"),
                sector=yahoo_data.get("sector", ""),
                industry=yahoo_data.get("industry", ""),
                market_cap=yahoo_data.get("market_cap"),
                volume=yahoo_data.get("volume"),
                pe_ratio=yahoo_data.get("pe_ratio"),
                dividend_yield=yahoo_data.get("dividend_yield"),
                last_updated=yahoo_data.get("last_updated", datetime.utcnow())
            )
            
            asset = await asset_service.create_asset(asset_data)
            created_assets.append(asset)
            print(f"   ✅ Created asset: {asset.ticker} - {asset.name} (${asset.current_price})")
            
        except Exception as e:
            print(f"   ❌ Error creating asset {ticker}: {e}")
            failed_tickers.append(ticker)
        
        # Small delay to avoid rate limiting
        await asyncio.sleep(0.3)
    
    return created_assets, skipped_assets, failed_tickers


async def main():
    """Main seeding function"""
    print("🌱 Starting smart database seeding...")
    print("=" * 60)
    
    # Check database connection first
    if not await check_database_connection():
        print("❌ Cannot proceed without database connection")
        sys.exit(1)
    
    try:
        # Get database session
        async with AsyncSessionLocal() as db_session:
            # Create admin user
            print("\n👤 Creating admin user...")
            admin_user = await create_admin_user(db_session)
            
            # Create sample clients
            print("\n👥 Creating sample clients...")
            clients, skipped_clients = await create_sample_clients(db_session)
            
            # Create assets from Yahoo Finance
            print("\n📈 Creating assets from Yahoo Finance...")
            assets, skipped_assets, failed_tickers = await fetch_and_create_assets(db_session, POPULAR_TICKERS)
            
            print("\n" + "=" * 60)
            print("🎉 Smart database seeding completed!")
            print(f"✅ Admin user: admin@betteredge.com (password: admin123)")
            print(f"✅ Clients: {len(clients)} total ({len(clients) - skipped_clients} created, {skipped_clients} already existed)")
            print(f"✅ Assets: {len(assets)} total ({len(assets) - skipped_assets} created, {skipped_assets} already existed)")
            
            if failed_tickers:
                print(f"❌ Failed to fetch {len(failed_tickers)} assets:")
                for ticker in failed_tickers:
                    print(f"   - {ticker}")
            
            print("\n📚 You can now:")
            print("   - Login with admin credentials")
            print("   - View assets in the API")
            print("   - Create portfolios for clients")
            print("   - Access API docs at: http://localhost:8000/docs")
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())