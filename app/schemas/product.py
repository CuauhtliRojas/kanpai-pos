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

