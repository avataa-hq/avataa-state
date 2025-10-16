from enum import Enum

from v1.models.kpi import KpiValTypes


class AvailableKPIAggregations(str, Enum):
    AVG = "avg"
    MAX = "max"
    MIN = "min"
    MOST_FREQUENT = "most_frequent"


class AvailableAggrKPIValTypes(str, Enum):
    INT = KpiValTypes.INT.value
    FLOAT = KpiValTypes.FLOAT.value
    STRING = KpiValTypes.STR.value
