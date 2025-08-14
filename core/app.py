# core/app.py
"""
Metro Match — Core FastAPI Application (Phase 3.2)

- Provides a /health endpoint
- Loads asset categories (logs count)
- Registers optional middlewares (safe if modules missing)
- Includes Database Admin routes with SINGLE prefix: /api/database/...
"""

from datetime import datetime
from fastapi import FastAPI

# ---- Logging (safe import) ----
try:
    from utils.logger import logger
except Exception:  # pragma: no cover
    import logging
    logger = logging.getLogger("core.app")
    logger.setLevel(logging.INFO)

# ---- Settings (optional; not required to run) ----
try:
    from core.config import settings
except Exception:
    class _S:
        ENV = "development"
        DEBUG = True
        API_VERSION = "v1"
    settings = _S()

# ---- Routers ----
# IMPORTANT: the router we import here MUST have NO prefix inside the file.
# We apply the single '/api/database' prefix right here when including it.
from api.routes.database_admin import router as database_router

# ---- Optional: asset category manager for Phase 3.2 demo logs ----
def _init_categories_if_available():
    try:
        from logic.asset_categories import asset_category_manager
        # Touch the manager to trigger any lazy init work and log counts
        total = len(getattr(asset_category_manager, "categories", {}))
        logger.info("Asset category system loaded with %d categories", total)
        print(f"✅ Asset categories loaded: {total} categories")
    except Exception as e:  # soft-fail; app should still start
        logger.warning("Asset categories not available: %s", e)


# ---- Optional middlewares (all soft-fail) ----
def _register_middlewares(app: FastAPI) -> None:
    # Request context
    try:
        from middleware.request_context import RequestContextMiddleware
        app.add_middleware(RequestContextMiddleware)
    except Exception as e:
        logger.debug("RequestContextMiddleware not registered: %s", e)

    # Rate limiter
    try:
        from middleware.rate_limiter import RateLimiterMiddleware
        app.add_middleware(RateLimiterMiddleware)
    except Exception as e:
        logger.debug("RateLimiterMiddleware not registered: %s", e)

    # Loop control (hardened bypass lives in api/looper.py or middleware.loop_control)
    try:
        # Prefer your dedicated middleware module if present
        try:
            from middleware.loop_control import LoopControlMiddleware  # type: ignore
        except Exception:
            # Fallback to api.looper middleware class
            from api.looper import LoopControlMiddleware  # type: ignore
        app.add_middleware(LoopControlMiddleware)
    except Exception as e:
        logger.debug("LoopControlMiddleware not registered: %s", e)

    # Kill switch (optional)
    try:
        from middleware.kill_switch import KillSwitchMiddleware
        app.add_middleware(KillSwitchMiddleware)
    except Exception as e:
        logger.debug("KillSwitchMiddleware not registered: %s", e)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Metro Match - Phase 3.2 Database Ready",
        version="3.2.0",
        description="Enterprise-grade backend for Metro Match marketplace platform",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # ---- Health route (root) ----
    @app.get("/health", tags=["default"], summary="Health Check")
    async def health():
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "3.2.0",
            "phase": "Phase 3.2 - Database Schema Design",
            "components": {
                "asset_categories": True,
                "database_admin": True,
            },
        }

    # ---- Optional init & middlewares ----
    _init_categories_if_available()
    _register_middlewares(app)

    # ---- Routers with SINGLE prefix here ----
    # The database_admin router file must declare: router = APIRouter(tags=[...])  (NO prefix!)
    app.include_router(database_router, prefix="/api/database")

    logger.info("Database admin routes loaded successfully")
    logger.info("Metro Match application initialized successfully")
    return app


# FastAPI entrypoint
app = create_app()
