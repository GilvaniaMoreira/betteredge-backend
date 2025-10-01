from .auth import router as auth_router
from .clients import router as clients_router
from .assets import router as assets_router

__all__ = [
    "auth_router",
    "clients_router", 
    "assets_router"
]

