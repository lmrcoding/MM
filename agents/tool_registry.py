TOOL_METADATA = {
    "InventoryCheck": {
        "description": "Checks current inventory levels for a given product.",
        "allowed_tiers": ["basic", "pro", "admin"],
        "risk_level": "low",
        "dry_run": False
    },
    "VendorMatch": {
        "description": "Finds vendors by category and region.",
        "allowed_tiers": ["pro", "admin"],
        "risk_level": "medium",
        "dry_run": False
    },
    "RefillRequest": {
        "description": "Triggers a refill order for low-stock items.",
        "allowed_tiers": ["admin"],
        "risk_level": "high",
        "dry_run": True
    }
}
