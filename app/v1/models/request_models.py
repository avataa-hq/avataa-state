from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from v1.routers.kpi_value.enum_models import AvailableKPIAggregations


class KPIAggrRequest(BaseModel):
    kpi_id: int = Field(gt=0)
    object_ids: List[int]
    granularity_id: int = Field(gt=0)
    aggregation_type: AvailableKPIAggregations
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
