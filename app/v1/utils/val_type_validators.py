from v1.models.kpi import KpiValTypes
from datetime import datetime


def int_validation(value):
    try:
        int(value)
        return value
    except BaseException:
        raise ValueError(f"Incorrect value for int val_type = {value}")


def float_validation(value):
    try:
        float(value)
        return value
    except BaseException:
        raise ValueError(f"Incorrect value for float val_type = {value}")


def bool_validation(value):
    expected = {"False": "False", "True": "True"}
    if value in expected:
        return value
    raise ValueError(
        f"Incorrect value for bool val_type = {value}. Must be True of False"
    )


def str_validation(value):
    return value


def date_validation(value):
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return
    except BaseException:
        raise ValueError(
            f"Incorrect value for date val_type = {value}. Date must be like "
            "'%Y-%m-%d'"
        )


def datetime_validation(value):
    try:
        datetime.fromisoformat(value)
        return value
    except BaseException:
        raise ValueError(
            f"Incorrect value for datetime val_type = {value}. Datetime "
            "must be like '%Y-%m-%dT%H:%M:%S.%fZ'"
        )


VALIDATION_FUNCTIONS = {
    KpiValTypes.INT.value: int_validation,
    KpiValTypes.FLOAT.value: float_validation,
    KpiValTypes.BOOL.value: bool_validation,
    KpiValTypes.STR.value: str_validation,
    KpiValTypes.DATE.value: date_validation,
    KpiValTypes.DATETIME.value: datetime_validation,
}


def get_validate_func_by_val_type(val_type: str):
    """Returns callable object of validation function, otherwise raises NotImplementedError."""
    validate_func = VALIDATION_FUNCTIONS.get(val_type)

    if not validate_func:
        raise NotImplementedError(
            f"Validation function for val_type = {val_type} not implemented"
        )
    return validate_func


def validate_value_by_val_type(val_type: str, value):
    """Returns valid value, otherwise raises error."""
    validate_func = get_validate_func_by_val_type(val_type)
    return validate_func(value)


def validate_iterable_inst(ints: iter, validate_func: callable):
    if not isinstance(ints, list):
        raise ValueError(
            f"Incorrect value - {ints}. Multiple value must be an array!"
        )
    res = []
    for item in ints:
        res.append(validate_func(item))
    return res


def get_value_validate_funct_for_kpi(
    kpi_val_type: KpiValTypes, kpi_multiple: bool
):
    """Returns validate func based on KPI.multiple and KPI.val_type"""
    valid_item_func = get_validate_func_by_val_type(kpi_val_type)
    if kpi_multiple:
        return lambda iter_inst: validate_iterable_inst(
            iter_inst, valid_item_func
        )
    else:
        return valid_item_func
