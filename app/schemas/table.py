from pydantic import BaseModel, ConfigDict


class TableResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    table_code: str
    display_name: str
    status_cache: str
    active: bool
