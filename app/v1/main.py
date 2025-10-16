from fastapi import Depends

from common_security.security import oauth2_scheme
from common_settings.config import PREFIX, TITLE, DEBUG
from init_app import create_app
from v1.routers.kpi.routers import router as kpi_router
from v1.routers.kpi_value.routers import router as kpi_value_router
from v1.routers.object_state.routers import router as object_sate_router
from v1.routers.batch.routers import router as batch_router
from v1.routers.granularity.routers import router as granularity_router
from v1.security.routers.kpi_routers import router as security_router
from v1.routers.palette.routers import router as palette_router
from v1.security.data import listener  # noqa

version = "1"
prefix = f"{PREFIX}/v{version}"

if DEBUG:
    app = create_app(root_path=prefix, title=TITLE, version=version)
else:
    app = create_app(
        root_path=prefix,
        title=TITLE,
        version=version,
        dependencies=[Depends(oauth2_scheme)],
    )

app.include_router(kpi_router)
app.include_router(granularity_router)
app.include_router(kpi_value_router)
app.include_router(object_sate_router)
app.include_router(batch_router)
app.include_router(security_router)
app.include_router(palette_router)
