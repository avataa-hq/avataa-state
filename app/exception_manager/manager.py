class ValidationError(Exception):
    """Base validation error"""

    pass


class NotFoundError(Exception):
    """Exception raised when an KPI is not found"""

    pass


class KPIUpdateError(Exception):
    """Exception during KPI update something happened"""

    pass


class KPIRelatedValidationError(ValidationError):
    """There are exist options to be "related KPI". So if kpi out of these
    options - it raise error"""

    pass


class KPILinkValidationError(ValidationError):
    """Error raised when parent or child cannot be set!"""

    pass
