from typing import Optional

from pydantic import BaseModel, Field


class GranularityBaseModel(BaseModel):
    id: int


class GranularityCreateModel(BaseModel):
    kpi_id: int = Field(gt=0)
    name: str = Field(min_length=1)
    seconds: Optional[int] = None


class GranularityInfoModel(GranularityCreateModel, GranularityBaseModel):
    pass


class GranularityUpdateModel(BaseModel):
    name: str = Field(min_length=1)
