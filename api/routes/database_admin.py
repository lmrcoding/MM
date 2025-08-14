# api/routes/database_admin.py - Database Administration API (Phase 3.2) - FIXED VERSION
"""
🔧 Metro Match - Database Administration API (Phase 3.2)
API endpoints for managing database schema, migrations, and monitoring

Updated to remove router-level prefix to avoid double '/api/database' in paths.
Keep the '/api/database' prefix ONLY in core/app.py when including this router.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

# Import existing components with fallbacks
try:
    from utils.logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

try:
    from utils.agent_rbac import require_role, UserRole
    HAS_RBAC = True
except ImportError:
    logger.warning("RBAC not available - using fallback authentication")
    HAS_RBAC = False

    # Fallback authentication
    def require_role(role):
        def decorator():
            return True  # Simplified for now
        return decorator

    class UserRole:
        ADMIN = "admin"

try:
    from config.database_schema import DatabaseAssetCategoryManager, setup_database_schema
except ImportError as e:
    logger.warning(f"Database schema not available: {e}")
    DatabaseAssetCategoryManager = None
    setup_database_schema = None

try:
    from utils.database_migrations import (
        DatabaseMigrationManager,
        run_migration,
        quick_migration_status,
    )
except ImportError as e:
    logger.warning(f"Database migrations not available: {e}")
    DatabaseMigrationManager = None
    run_migration = None
    quick_migration_status = None

try:
    from config.supabase_client import get_supabase
except ImportError as e:
    logger.warning(f"Supabase client not available: {e}")
    get_supabase = None


# Pydantic models for API requests/responses
class MigrationRequest(BaseModel):
    """Request model for database migration"""
    dry_run: bool = Field(True, description="If true, validate without making changes")
    force: bool = Field(False, description="Force migration even if validation fails")
    backup_existing: bool = Field(True, description="Backup existing data before migration")


class DatabaseQuery(BaseModel):
    """Request model for database queries"""
    query: str = Field(..., description="Search query for asset categories")
    limit: int = Field(20, ge=1, le=100, description="Maximum number of results")
    category_type: Optional[str] = Field(None, description="Filter by category type")


class CategoryUpdate(BaseModel):
    """Request model for updating asset categories"""
    name: Optional[str] = Field(None, description="Updated category name")
    description: Optional[str] = Field(None, description="Updated description")
    is_active: Optional[bool] = Field(None, description="Updated active status")
    priority: Optional[int] = Field(None, ge=1, le=10, description="Updated priority")


class DatabaseStats(BaseModel):
    """Response model for database statistics"""
    total_categories: int
    active_categories: int
    total_assets: int
    total_vendors: int
    total_matches: int
    database_size_mb: float
    last_updated: datetime


# Router with NO prefix here (prefix is applied in core/app.py)
if HAS_RBAC:
    router = APIRouter(
        tags=["Database Administration"],
        dependencies=[require_role(UserRole.ADMIN)],
    )
else:
    router = APIRouter(tags=["Database Administration"])


@router.get("/status", response_model=Dict[str, Any])
async def get_database_status():
    """
    Get current database and migration status
    """
    try:
        logger.info("Checking database status...")

        if not quick_migration_status:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "status": "migration_system_not_available",
                "message": "Database migration system not properly configured",
                "system_ready": False,
            }

        # Get basic migration status
        migration_status = await quick_migration_status()

        # Get database health if available
        if get_supabase:
            supabase = get_supabase()
            health = await supabase.health_check()
            connection_info = supabase.get_connection_info()
        else:
            health = {"healthy": False, "error": "Supabase client not configured"}
            connection_info = {}

        status = {
            "timestamp": datetime.utcnow().isoformat(),
            "database_health": {
                "connected": health.get("healthy", False),
                "response_time_ms": health.get("response_time_ms", 0),
                "connection_info": connection_info,
            },
            "migration_status": migration_status,
            "system_ready": (
                migration_status.get("database_connected", False)
                and migration_status.get("database_has_categories", False)
            ),
        }

        logger.info(f"Database status check completed - System ready: {status['system_ready']}")
        return status

    except Exception as e:
        logger.error(f"Database status check failed: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "error",
            "error": str(e),
            "system_ready": False,
        }


@router.post("/migrate", response_model=Dict[str, Any])
async def run_database_migration(
    request: MigrationRequest,
    background_tasks: BackgroundTasks,
):
    """
    Run database migration
    """
    try:
        if not run_migration:
            raise HTTPException(
                status_code=503,
                detail="Migration system not available - please check configuration",
            )

        logger.info(f"Starting database migration - Dry run: {request.dry_run}")

        # Run migration
        migration_result = await run_migration(dry_run=request.dry_run)

        if migration_result["success"]:
            logger.info("✅ Database migration completed successfully")

            # If this was a real migration, schedule post-migration tasks
            if not request.dry_run:
                background_tasks.add_task(_post_migration_tasks)

        else:
            logger.error("❌ Database migration failed")

        return {
            "success": migration_result["success"],
            "dry_run": request.dry_run,
            "timestamp": datetime.utcnow().isoformat(),
            "migration_details": migration_result,
            "next_steps": migration_result.get("next_steps", []),
        }

    except Exception as e:
        logger.error(f"Migration endpoint failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Migration failed: {str(e)}",
        )


@router.get("/categories", response_model=Dict[str, Any])
async def get_database_categories(
    limit: int = 50,
    offset: int = 0,
    category_type: Optional[str] = None,
    active_only: bool = True,
):
    """
    Get asset categories from database (with memory fallback)
    """
    try:
        if not DatabaseAssetCategoryManager:
            # Fallback to memory-based categories
            try:
                from logic.asset_categories import asset_category_manager

                categories = []
                for cat_id, cat_data in asset_category_manager.categories.items():
                    if (
                        category_type
                        and hasattr(cat_data, "category_type")
                        and cat_data.category_type.value != category_type
                    ):
                        continue

                    categories.append(
                        {
                            "id": cat_id,
                            "name": cat_data.name,
                            "category_type": cat_data.category_type.value
                            if hasattr(cat_data, "category_type")
                            else "unknown",
                            "description": cat_data.description,
                            "source": "memory",
                        }
                    )

                # Apply pagination
                total_count = len(categories)
                paginated_categories = categories[offset : offset + limit]

                return {
                    "success": True,
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": "memory",
                    "pagination": {
                        "total": total_count,
                        "limit": limit,
                        "offset": offset,
                        "has_more": offset + limit < total_count,
                    },
                    "categories": paginated_categories,
                }

            except Exception as e:
                raise HTTPException(
                    status_code=503,
                    detail=f"Neither database nor memory categories available: {str(e)}",
                )

        logger.info(f"Getting database categories - limit: {limit}, offset: {offset}")

        # Use database manager
        db_manager = DatabaseAssetCategoryManager()

        # Get all categories
        all_categories = await db_manager.get_categories()

        # Apply filters
        filtered_categories = []
        for cat_id, cat_data in all_categories.items():
            # Filter by active status
            if active_only and not cat_data.get("is_active", True):
                continue

            # Filter by category type
            if category_type and cat_data.get("category_type") != category_type:
                continue

            filtered_categories.append({"id": cat_id, **cat_data})

        # Apply pagination
        total_count = len(filtered_categories)
        paginated_categories = filtered_categories[offset : offset + limit]

        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "database",
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count,
            },
            "categories": paginated_categories,
        }

    except Exception as e:
        logger.error(f"Get categories endpoint failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get categories: {str(e)}",
        )


@router.get("/health", response_model=Dict[str, Any])
async def database_health_check():
    """
    Comprehensive database health check
    """
    try:
        logger.info("Running database health check...")

        health_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_health": "unknown",
            "checks": {},
        }

        # Check 1: Basic connectivity
        if get_supabase:
            try:
                supabase = get_supabase()
                basic_health = await supabase.health_check()

                health_results["checks"]["connectivity"] = {
                    "status": "healthy"
                    if basic_health.get("healthy", False)
                    else "unhealthy",
                    "response_time_ms": basic_health.get("response_time_ms", 0),
                    "details": basic_health,
                }
            except Exception as e:
                health_results["checks"]["connectivity"] = {
                    "status": "unhealthy",
                    "error": str(e),
                }
        else:
            health_results["checks"]["connectivity"] = {
                "status": "unavailable",
                "message": "Supabase client not configured",
            }

        # Check 2: Memory categories (fallback)
        try:
            from logic.asset_categories import asset_category_manager

            health_results["checks"]["memory_categories"] = {
                "status": "healthy",
                "category_count": len(asset_category_manager.categories),
            }
        except Exception as e:
            health_results["checks"]["memory_categories"] = {
                "status": "unhealthy",
                "error": str(e),
            }

        # Determine overall health
        check_statuses = [check.get("status", "unhealthy") for check in health_results["checks"].values()]
        healthy_checks = sum(1 for status in check_statuses if status == "healthy")
        total_checks = len(check_statuses)

        if healthy_checks == total_checks:
            health_results["overall_health"] = "healthy"
        elif healthy_checks >= total_checks * 0.5:
            health_results["overall_health"] = "degraded"
        else:
            health_results["overall_health"] = "unhealthy"

        health_results["health_score"] = healthy_checks / total_checks if total_checks > 0 else 0

        logger.info(f"Database health check completed - Overall: {health_results['overall_health']}")
        return health_results

    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_health": "error",
            "error": str(e),
        }


# Helper functions
async def _post_migration_tasks():
    """Background tasks to run after successful migration"""
    try:
        logger.info("Running post-migration tasks...")

        if get_supabase and DatabaseAssetCategoryManager:
            # Task 1: Update search indexes
            supabase = get_supabase()
            await supabase.execute_sql("ANALYZE asset_categories;")

            # Task 2: Cache warming
            db_manager = DatabaseAssetCategoryManager()
            await db_manager.get_categories(force_refresh=True)

        logger.info("✅ Post-migration tasks completed")

    except Exception as e:
        logger.error(f"Post-migration tasks failed: {e}")


# Export the router
__all__ = ["router"]
