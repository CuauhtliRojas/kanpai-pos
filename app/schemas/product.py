from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: str
    product_type: str
    name: str
    display_name: str
    category_id: int | None
    price_cents: int
    active: bool
    visible_pos: bool
    inventory_recipe_multiplier: Decimal
    image_path: str | None = None
    image_url: str | None = None
