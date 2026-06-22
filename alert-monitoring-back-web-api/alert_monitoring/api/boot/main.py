from dotenv import load_dotenv
load_dotenv()

import os
from pathlib import Path

from fwkpy_lib_fastapi import FastAPIBuilder
from fwkpy_lib_core.common.injector import Injector
from fwkpy_lib_utils.common.i18n.internationalization import load_translations, set_i18n
from fwkpy_lib_database.synchronous.middlewares import add_session_middleware
from fwkpy_lib_utils.synchronous.health_checks.health_checks_app import HealthChecksApp

from alert_monitoring.api.driving.api_rest.security import ApiKeyMiddleware
from alert_monitoring.api.driving.api_rest.adapters import (
    sync_adapter,
    alert_app_adapter,
    alert_api_adapter,
    silences_adapter,
    catalog_adapter,
    catalog_app_api_adapter,
)

set_i18n()
translations_path = Path(os.path.dirname(__file__))
load_translations(os.path.join(translations_path, 'resources/i18n'))

Injector.preload_all_classes()

app = FastAPIBuilder()

app.include_router(sync_adapter.router)
app.include_router(alert_app_adapter.router)
app.include_router(alert_api_adapter.router)
app.include_router(silences_adapter.router)
app.include_router(catalog_adapter.router)
app.include_router(catalog_app_api_adapter.router)

app.add_middleware(ApiKeyMiddleware, api_key=os.getenv("API_KEY"))
add_session_middleware(app)
HealthChecksApp().start(fastapi_app=app)