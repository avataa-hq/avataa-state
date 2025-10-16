from v1.security.security_data_models import ClientRoles, UserData
from v1.settings.config import DEFAULT_ADMIN_ROLE


def get_admin_user_model():
    return UserData(
        id=None,
        audience=None,
        name="Anonymous",
        preferred_name="Anonymous",
        realm_access=ClientRoles(
            name="realm_access", roles=[DEFAULT_ADMIN_ROLE]
        ),
        resource_access=None,
        groups=None,
    )
