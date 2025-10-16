from datetime import datetime
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field


class KPIValuesStates(Enum):
    CURRENT = "current"
    HISTORICAL = "historical"
    PLANNED = "planned"


class KPIValuesStatesPossibleToCreate(Enum):
    PLANNED = KPIValuesStates.PLANNED.value
    HISTORICAL = KPIValuesStates.HISTORICAL.value


class KPIValueModelBase(BaseModel):
    id: int = Field()


class KPIValuePlannedModelCreateByKPI(BaseModel):
    object_id: int = Field(gt=0)
    granularity_id: int = Field(gt=0)
    value: Any
    record_time: Optional[datetime]


class KPIValueHistoricalModelCreateByKPI(BaseModel):
    object_id: int = Field(gt=0)
    granularity_id: int = Field(gt=0)
    value: Any


class KPIValuePlannedModelUpdateByKPI(BaseModel):
    value: Any = None
    record_time: Optional[datetime] = None

    class Config:
        use_enum_values = True


class KPIValueModelInfo(KPIValuePlannedModelCreateByKPI, KPIValueModelBase):
    state: str
    pass

    class Config:
        from_attributes = True
