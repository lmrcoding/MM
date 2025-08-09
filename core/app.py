# core/app.py

from fastapi import FastAPI
from api import middleware_security
from api.routes import agent_routes, admin_routes, admin_monitor  # 👈 include the new route

def create_app() -> FastAPI:
    app = FastAPI(
        title="Metro Match API",
        version="1.0.0",
        description="Enterprise-grade AI Agent Platform for Resource & Inventory Matching",
    )

    # 🛡 Attach core middleware (security filters, rate limits, etc.)
    middleware_security.attach_middleware(app)

    # 🚏 Register routes
    app.include_router(agent_routes.router)
    app.include_router(admin_routes.router)
    app.include_router(admin_monitor.router)  # 👈 Register new system status route

    return app
