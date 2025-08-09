from pydantic import BaseModel, Field
from typing import Optional

class InventoryCheckInput(BaseModel):
    product_id: str = Field(..., description="Unique product identifier")
    location_id: Optional[str] = Field(None, description="Optional warehouse/store location")

class RefillRequestInput(BaseModel):
    product_id: str = Field(..., description="Product to refill")
    quantity: int = Field(..., gt=0, description="How many units to refill")
    urgency: Optional[str] = Field("normal", description="Refill priority (normal/high/emergency)")

class VendorMatchInput(BaseModel):
    category: str = Field(..., description="Type of vendor needed (e.g., cleaning, food)")
    region: Optional[str] = Field(None, description="Preferred vendor region")
