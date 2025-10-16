from ast import literal_eval

from v1.database.schemas import KPIValue
from v1.models.kpi import KpiValTypes


def convert_from_str_to_int(value: str):
    return int(value)


def convert_from_str_to_float(value: str):
    return float(value)


def convert_from_str_to_bool(value: str):
    bool_dict = {"False": False, "True": True}
    return bool_dict.get(value)


def convert_from_str_to_str(value: str):
    return value


def convert_from_str_to_date(value: str):
    return value


def convert_from_str_to_datetime(value: str):
    return value


DESERIALIZATION_FUNCTIONS = {
    KpiValTypes.INT.value: convert_from_str_to_int,
    KpiValTypes.FLOAT.value: convert_from_str_to_float,
    KpiValTypes.BOOL.value: convert_from_str_to_bool,
    KpiValTypes.STR.value: convert_from_str_to_str,
    KpiValTypes.DATE.value: convert_from_str_to_date,
    KpiValTypes.DATETIME.value: convert_from_str_to_datetime,
}


def get_deserialization_func_by_val_type(val_type: str):
    """Returns callable object of deserialization function, otherwise raises NotImplementedError."""
    deserializer_func = DESERIALIZATION_FUNCTIONS.get(val_type)

    if not deserializer_func:
        raise NotImplementedError(
            f"Deserialization function for val_type = {val_type} not implemented"
        )
    return deserializer_func


def deserialize_value_by_val_type(val_type: str, value):
    """Returns deserialized value, otherwise raises error."""
    deserializer = get_deserialization_func_by_val_type(val_type)
    return deserializer(value)


def multiple_deserializer(value: str):
    return literal_eval(value)


def get_deserializer_func_for_kpi(
    kpi_val_type: KpiValTypes, kpi_multiple: bool
):
    """Returns deserializer based on KPI.multiple and KPI.val_type"""
    if kpi_multiple:
        return multiple_deserializer
    else:
        return get_deserialization_func_by_val_type(kpi_val_type)


def get_deserialized_kpi_value_inst(
    kpi_value: KPIValue, deserializer: callable
):
    """Returns deserialized KPIValue inst"""
    kpi_value.value = deserializer(kpi_value.value)
    return kpi_value
