#!/usr/bin/env python3
"""
Script simples de seed do banco de dados para BetterEdge Backend
Execute com: python seed.py
"""

import asyncio
import sys
from pathlib import Path

# Adicionar o diretório raiz do projeto ao path do Python
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import asyncio
import sys
import os
from pathlib import Path

# Adicionar o diretório raiz do projeto ao path do Python
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


# Tickers populares para seed
POPULAR_TICKERS = [
    # Ações dos EUA
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX", "AMD", "INTC",
    "JPM", "BAC", "WMT", "PG", "JNJ", "V", "MA", "DIS", "PYPL", "ADBE",
    
    # Ações Brasileiras (B3) - Usando sufixo .SA para Yahoo Finance
    "VALE3.SA", "PETR4.SA", "ITUB4.SA", "BBDC4.SA", "ABEV3.SA", "MGLU3.SA", "WEGE3.SA", "RENT3.SA", "SUZB3.SA", "B3SA3.SA",
    "LREN3.SA", "JBSS3.SA", "RADL3.SA", "PETR3.SA", "BBAS3.SA", "BOVA11.SA", "SMAL11.SA", "IVVB11.SA",
    
    # ETFs
    "SPY", "QQQ", "VTI", "VOO", "ARKK", "TQQQ", "SOXL",
    
    # Criptomoedas (se disponível)
    "BTC-USD", "ETH-USD", "ADA-USD"
]


async def check_database_connection():
    """Verificar se o banco de dados está acessível"""
    try:
        async with AsyncSessionLocal() as db_session:
            # Apenas tentar criar uma sessão - isso testará a conexão
            print("Conexão com banco de dados bem-sucedida")
            return True
    except Exception as e:
        print(f"Falha na conexão com banco de dados: {e}")
        return False


async def create_admin_user(db_session):
    """Criar usuário administrador"""
    auth_service = AuthService(db_session)
    
    admin_email = "admin@betteredge.com"
    
    # Verificar se admin já existe
    existing_admin = await auth_service.get_user_by_email(admin_email)
    if existing_admin:
        print(f"Usuário admin já existe: {admin_email}")
        return existing_admin
    
    # Criar usuário admin
    admin_data = UserCreate(
        email=admin_email,
        password="admin123"  # Mude isso em produção!
    )
    
    admin_user = await auth_service.create_user(admin_data)
    print(f"Usuário admin criado: {admin_email} (ID: {admin_user.id})")
    print(f"   Senha: admin123")
    return admin_user


async def create_sample_clients(db_session):
    """Criar clientes de exemplo"""
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
        # Verificar se cliente já existe
        existing_client = await client_service.get_client_by_email(client_data["email"])
        if existing_client:
            print(f"Cliente já existe: {client_data['name']} ({client_data['email']})")
            created_clients.append(existing_client)
            skipped_clients += 1
            continue
        
        # Criar cliente
        client_create = ClientCreate(**client_data)
        client = await client_service.create_client(client_create)
        created_clients.append(client)
        print(f"Cliente criado: {client.name} ({client.email})")
    
    return created_clients, skipped_clients


async def fetch_and_create_assets(db_session, tickers):
    """Buscar ativos do Yahoo Finance e criá-los no banco de dados"""
    asset_service = AssetService(db_session)
    
    created_assets = []
    skipped_assets = 0
    failed_tickers = []
    
    print(f"Processando {len(tickers)} ativos do Yahoo Finance...")
    
    for i, ticker in enumerate(tickers, 1):
        print(f"[{i}/{len(tickers)}] Processando {ticker}...")
        
        # Verificar se ativo já existe
        existing_asset = await asset_service.get_asset_by_ticker(ticker)
        if existing_asset:
            print(f"   Ativo já existe: {ticker}")
            created_assets.append(existing_asset)
            skipped_assets += 1
            continue
        
        # Buscar dados detalhados do Yahoo Finance usando novo sistema
        yahoo_data = await asset_service.get_yahoo_asset_details(ticker)
        
        if not yahoo_data:
            print(f"   Falha ao buscar dados para {ticker}")
            failed_tickers.append(ticker)
            continue
        
        # Criar ativo
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
            print(f"   Ativo criado: {asset.ticker} - {asset.name} (${asset.current_price})")
            
        except Exception as e:
            print(f"   Erro ao criar ativo {ticker}: {e}")
            failed_tickers.append(ticker)
        
        # Pequeno delay para evitar rate limiting
        await asyncio.sleep(0.3)
    
    return created_assets, skipped_assets, failed_tickers


async def main():
    """Função principal de seed"""
    print("Iniciando seed do banco de dados...")
    print("=" * 60)
    
    # Verificar conexão com banco de dados primeiro
    if not await check_database_connection():
        print("Não é possível prosseguir sem conexão com banco de dados")
        sys.exit(1)
    
    try:
        # Obter sessão do banco de dados
        async with AsyncSessionLocal() as db_session:
            # Criar usuário admin
            print("\nCriando usuário admin...")
            admin_user = await create_admin_user(db_session)
            
            # Criar clientes de exemplo
            print("\nCriando clientes de exemplo...")
            clients, skipped_clients = await create_sample_clients(db_session)
            
            # Criar ativos do Yahoo Finance
            print("\nCriando ativos do Yahoo Finance...")
            assets, skipped_assets, failed_tickers = await fetch_and_create_assets(db_session, POPULAR_TICKERS)
            
            print("\n" + "=" * 60)
            print("Seed do banco de dados concluído!")
            print(f"Usuário admin: admin@betteredge.com (senha: admin123)")
            print(f"Clientes: {len(clients)} total ({len(clients) - skipped_clients} criados, {skipped_clients} já existiam)")
            print(f"Ativos: {len(assets)} total ({len(assets) - skipped_assets} criados, {skipped_assets} já existiam)")
            
            if failed_tickers:
                print(f"Falha ao buscar {len(failed_tickers)} ativos:")
                for ticker in failed_tickers:
                    print(f"   - {ticker}")
            
            print("\nAgora você pode:")
            print("   - Fazer login com credenciais de admin")
            print("   - Visualizar ativos na API")
            print("   - Criar portfólios para clientes")
            print("   - Acessar docs da API em: http://localhost:8000/docs")
        
    except Exception as e:
        print(f"\nErro durante o seed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())