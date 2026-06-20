from pydantic import BaseModel, ConfigDict


class VariantOptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    variant_group_id: int
    product_id: int | None
    name: str
    sku: str | None
    price_delta_cents: int
    station_id: int | None
    active: bool


class VariantGroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    name: str
    min_select: int
    max_select: int
    required: bool
    active: bool
    options: list[VariantOptionResponse]
