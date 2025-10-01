from .auth import router as auth_router
from .clients import router as clients_router
from .assets import router as assets_router
from .allocations import router as allocations_router

__all__ = [
    "auth_router",
    "clients_router", 
    "assets_router",
    "allocations_router"
]

