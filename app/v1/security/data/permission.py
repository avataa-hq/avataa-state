from collections import namedtuple

from v1.database.schemas import KPI, KPIPermission

Permission = namedtuple("Permission", ["main", "security", "column"])


db_permissions = {
    KPI.__tablename__: Permission(main=KPI, security=KPIPermission, column="id")
}

db_admins = {"realm_access.__admin"}
