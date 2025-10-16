from enum import Enum
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class KpiValTypes(Enum):
    INT = "int"
    STR = "str"
    FLOAT = "float"
    BOOL = "bool"
    DATE = "date"
    DATETIME = "datetime"


class KPIModelBase(BaseModel):
    id: int = Field()


class KPIModelCreate(BaseModel):
    name: str = Field(min_length=1)
    description: Optional[str] = None
    label: Optional[str]
    branch: Optional[str]
    group: Optional[str] = None
    val_type: KpiValTypes
    multiple: Optional[bool] = Field(default=False)
    object_type: Optional[int] = None
    related_kpis: List[int] = None
    parent_kpi: Optional[int] = Field(default=None, gt=0)
    child_kpi: Optional[int] = Field(default=None, gt=0)

    class Config:
        use_enum_values = True


class KPIModelInfo(KPIModelCreate, KPIModelBase):
    pass


class KPIModelPartialUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    label: Optional[str] = None
    branch: Optional[str]
    val_type: Optional[KpiValTypes] = None
    object_type: Optional[int] = None
    related_kpis: List[int] = None
    group: Optional[str] = None
    parent_kpi: Optional[int] = Field(default=None, gt=0)
    child_kpi: Optional[int] = Field(default=None, gt=0)

    class Config:
        use_enum_values = True


class KPIWithTMO(BaseModel):
    kpi_id: int
    object_type_id: int


class SetCustomPalette(BaseModel):
    object_type_id: int
    val_type: str
    kpi_id: int
    kpi_name: str
    palette: Dict


class RelatedKPIsWithTMO(BaseModel):
    related_kpis: List[KPIWithTMO]
