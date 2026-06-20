from pydantic import BaseModel, ConfigDict


class BusinessSettingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    business_name: str
    currency: str
    tax_enabled: bool
    tax_rate_bps: int
    tax_included: bool
    tax_label: str
