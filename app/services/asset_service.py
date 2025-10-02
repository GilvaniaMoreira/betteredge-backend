from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from app.models.asset import Asset
from app.schemas.asset import AssetCreate
from typing import Optional, Tuple, Dict, Any
from datetime import datetime
import yfinance as yf
import asyncio


class AssetService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_asset(self, asset_data: AssetCreate) -> Asset:
        db_asset = Asset(**asset_data.dict())
        self.db.add(db_asset)
        await self.db.commit()
        await self.db.refresh(db_asset)
        return db_asset

    async def get_asset(self, asset_id: int) -> Asset | None:
        result = await self.db.execute(
            select(Asset).where(Asset.id == asset_id)
        )
        return result.scalar_one_or_none()

    async def get_asset_by_ticker(self, ticker: str) -> Asset | None:
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
        query = select(Asset)
        count_query = select(func.count(Asset.id))

        if search:
            search_filter = or_(
                Asset.ticker.ilike(f"%{search}%"),
                Asset.name.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        assets = result.scalars().all()
        
        return list(assets), total


    async def search_yahoo_assets_by_name(self, query: str, limit: int = 10) -> list[Dict[str, Any]]:
        """Buscar ativos do Yahoo Finance e retornar resultados simplificados para autocomplete"""
        try:
            print(f"Buscando ativos com query: '{query}', limite: {limit}")
            
            # Usar yfinance.Search para busca flexível
            loop = asyncio.get_event_loop()
            search_results = await loop.run_in_executor(None, self._search_yahoo_finance, query, limit)
            
            if not search_results:
                return []
            
            # Processar resultados da busca - simplificado para autocomplete
            processed_results = []
            for quote in search_results:
                result = {
                    "ticker": quote.get("symbol", "").upper(),
                    "name": quote.get("longname", quote.get("shortname", quote.get("symbol", ""))),
                    "exchange": quote.get("exchDisp", quote.get("exchange", "Unknown"))
                }
                
                processed_results.append(result)
            
            print(f"Retornando {len(processed_results)} resultados de busca simplificados")
            return processed_results
            
        except Exception as e:
            print(f"Erro ao buscar ativos do Yahoo Finance: {e}")
            return []

    async def get_yahoo_asset_details(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Obter informações detalhadas para um ticker específico usando yfinance.Ticker"""
        try:
            print(f"Buscando informações detalhadas para ticker: {ticker}")
            
            # Usar yfinance.Ticker para informações detalhadas
            loop = asyncio.get_event_loop()
            ticker_data = await loop.run_in_executor(None, self._get_yahoo_ticker_info, ticker)
            
            if not ticker_data:
                return None
            
            # Verificar se temos dados significativos (não apenas padrões)
            if not ticker_data.get("longName") and not ticker_data.get("shortName"):
                return None
            
            # Extrair dados detalhados
            result = {
                "ticker": ticker.upper(),
                "name": ticker_data.get("longName", ticker_data.get("shortName", ticker)),
                "exchange": ticker_data.get("exchange", "Unknown"),
                "currency": ticker_data.get("currency", "USD"),
                "current_price": ticker_data.get("currentPrice") or ticker_data.get("regularMarketPrice"),
                "sector": ticker_data.get("sector", ""),
                "industry": ticker_data.get("industry", ""),
                "market_cap": ticker_data.get("marketCap"),
                "volume": ticker_data.get("volume") or ticker_data.get("regularMarketVolume"),
                "pe_ratio": ticker_data.get("trailingPE"),
                "dividend_yield": ticker_data.get("dividendYield"),
                "last_updated": datetime.utcnow()
            }
            
            print(f"Detalhes obtidos com sucesso para {ticker}")
            return result
            
        except Exception as e:
            print(f"Erro ao buscar detalhes do ativo Yahoo para {ticker}: {e}")
            return None

    def _search_yahoo_finance(self, query: str, limit: int):
        """Função síncrona para buscar no Yahoo Finance usando yfinance.Search"""
        try:
            # Usar yfinance.Search para busca flexível
            search = yf.Search(query, max_results=limit)
            search_results = search.search()
            

            # Obter cotações dos resultados da busca
            quotes = search_results.quotes if hasattr(search_results, 'quotes') else []
            print(f"Cotações: {quotes}")  
            
            return quotes[:limit] if quotes else []
            
        except Exception as e:
            print(f"Erro ao buscar no Yahoo Finance para {query}: {e}")
            return []

    def _get_yahoo_ticker_info(self, ticker: str):
        """Função síncrona para obter informações do ticker do Yahoo Finance"""
        try:
            ticker_obj = yf.Ticker(ticker)
            return ticker_obj.info if ticker_obj.info else None
        except Exception as e:
            print(f"Erro ao obter informações do Yahoo para {ticker}: {e}")
            return None

