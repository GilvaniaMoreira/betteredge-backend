from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import auth_router, clients_router, assets_router, allocations_router, transactions_router

app = FastAPI(
    title="BetterEdge Investment Platform API",
    description="A comprehensive investment management platform API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(clients_router)
app.include_router(assets_router)
app.include_router(allocations_router)
app.include_router(transactions_router)


@app.get("/")
async def root():
    return {"message": "BetterEdge Investment Platform API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

