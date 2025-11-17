# Object State

Microservices stores historical information about objects and their parameter values.

## Environment variables

```toml
DEBUG=<True/False>
DOCS_CUSTOM_ENABLED=<True/False>
DOCS_REDOC_JS_URL=<redoc_js_url>
DOCS_SWAGGER_CSS_URL=<swagger_css_url>
DOCS_SWAGGER_JS_URL=<swagger_js_url>
FRONTEND_SETTINGS_GRPC_PORT=<frontend_settings_grpc_port>
FRONTEND_SETTINGS_HOST=<frontend_settings_host>
KEYCLOAK_CLIENT_ID=<keycloak_object_state_client>
KEYCLOAK_CLIENT_SECRET=<keycloak_object_state_client_secret>
KEYCLOAK_HOST=<keycloak_host>
KEYCLOAK_PORT=<keycloak_port>
KEYCLOAK_PROTOCOL=<keycloak_protocol>
KEYCLOAK_REALM=avataa
KEYCLOAK_REDIRECT_HOST=<keycloak_external_host>
KEYCLOAK_REDIRECT_PORT=<keycloak_external_port>
KEYCLOAK_REDIRECT_PROTOCOL=<keycloak_external_protocol>
UVICORN_WORKERS=<uvicorn_workers_number>
V1_DB_HOST=<pgbouncer/postgres_host>
V1_DB_NAME=<pgbouncer/postgres_object_state_db_name>
V1_DB_PASS=<pgbouncer/postgres_object_state_password>
V1_DB_PORT=<pgbouncer/postgres_port>
V1_DB_TYPE=postgresql+asyncpg
V1_DB_USER=<pgbouncer/postgres_object_state_user>
```


### Explanation

#### General

- KEYCLOAK_HOST
- KEYCLOAK_PORT
- KEYCLOAK_REALM
- KEYCLOAK_CLIENT_ID
- KEYCLOAK_CLIENT_SECRET
- DEBUG - enables debug mode (disabled authorization, enabled CORS for all sources)

#### Database

- V1_DB_TYPE - driver for database (must be async)
- V1_DB_HOST
- V1_DB_PORT
- V1_DB_USER
- V1_DB_PASS
- V1_DB_NAME

#### Compose

- `REGISTRY_URL` - Docker regitry URL, e.g. `harbor.domain.com`
- `PLATFORM_PROJECT_NAME` - Docker regitry project Docker image can be downloaded from, e.g. `avataa`

## Run command
``uvicorn main:app [options]``
> Note: if running without `alembic upgrade head` MS will start with empty sources




Export Compliance

This Software, including any source code, technology, and technical data, is distributed under the Apache License, Version 2.0.

Users of this Software are solely responsible for compliance with all applicable national and international laws, regulations, and restrictions pertaining to export, re-export, or import. This includes, but is not limited to, the U.S. Export Administration Regulations (EAR) and restrictions concerning embargoed countries and restricted party lists.

By downloading, accessing, or using this Software, you affirm that:

1.  You are not located in a country that is subject to a U.S. government embargo or has been designated by the U.S. government as a "terrorist supporting" country.
2.  You are not listed on any U.S. government list of prohibited or restricted parties (e.g., the Specially Designated Nationals List or the Denied Persons List).
