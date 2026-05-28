from aiogram import Router

# Import individual handlers
from . import start
from . import analyze
from . import market
from . import help as help_handlers
from . import payments
from . import journal
from . import upload
from . import admin

# Create routers
start_router = start.router
analyze_router = analyze.router
market_router = market.router
help_router = help_handlers.router
payments_router = payments.router
journal_router = journal.router
upload_router = upload.router
admin_router = admin.router

__all__ = [
    "start_router", 
    "analyze_router", 
    "market_router", 
    "help_router",
    "payments_router",
    "journal_router",
    "upload_router",
    "admin_router"
]
