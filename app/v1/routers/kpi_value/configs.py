from sqlalchemy import func, Integer, Float, String, Boolean, Date, DateTime

from v1.models.kpi import KpiValTypes
from v1.routers.kpi_value.enum_models import AvailableKPIAggregations

AGGREGATION_CORRESPONDING_TABLE = {
    AvailableKPIAggregations.AVG.value: func.avg,
    AvailableKPIAggregations.MAX.value: func.max,
    AvailableKPIAggregations.MIN.value: func.min,
}

CORRESPONDING_SQL_CAST_TYPE_TABLE = {
    KpiValTypes.INT.value: Integer,
    KpiValTypes.FLOAT.value: Float,
    KpiValTypes.STR.value: String,
    KpiValTypes.BOOL.value: Boolean,
    KpiValTypes.DATE.value: Date,
    KpiValTypes.DATETIME.value: DateTime,
}
