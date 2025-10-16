from v1.database.schemas import KPIValue
from v1.models.kpi import KpiValTypes
from datetime import datetime


def convert_to_int(value: str):
    return int(value)


def convert_to_float(value: str):
    return float(value)


def convert_to_bool(value: str):
    bool_dict = {"False": False, "True": True}
    return bool_dict.get(value)


def convert_to_str(value: str):
    return str(value)


def convert_to_date(value: str):
    date = datetime.fromisoformat(value)
    return date.date()


def convert_to_datetime(value: str):
    return datetime.fromisoformat(value)


SERIALIZATION_FUNCTIONS = {
    KpiValTypes.INT.value: convert_to_int,
    KpiValTypes.FLOAT.value: convert_to_float,
    KpiValTypes.BOOL.value: convert_to_bool,
    KpiValTypes.STR.value: convert_to_str,
    KpiValTypes.DATE.value: convert_to_date,
    KpiValTypes.DATETIME.value: convert_to_datetime,
}


def get_serialization_func_by_val_type(val_type: str):
    """Returns callable object of serialization function, otherwise raises NotImplementedError."""
    serializer_func = SERIALIZATION_FUNCTIONS.get(val_type)

    if not serializer_func:
        raise NotImplementedError(
            f"Serialization function for val_type = {val_type} not implemented"
        )
    return serializer_func


def serialize_value_by_val_type(val_type: str, value):
    """Returns serialized value, otherwise raises error."""
    serializer = get_serialization_func_by_val_type(val_type)
    return serializer(value)


def multiple_serializer(values: list, val_type: SERIALIZATION_FUNCTIONS):
    return [serialize_value_by_val_type(val_type, x) for x in values]


def get_serializer_func_for_kpi(kpi_val_type: KpiValTypes, kpi_multiple: bool):
    """Returns serializer based on KPI.multiple and KPI.val_type"""
    if kpi_multiple:
        return lambda x: str(multiple_serializer(x, kpi_val_type))
    else:
        return lambda x: str(x)


def get_serialized_kpi_value_inst(kpi_value: KPIValue, serializer: callable):
    """Returns serialized KPIValue inst"""
    kpi_value.value = serializer(kpi_value.value)
    return kpi_value
