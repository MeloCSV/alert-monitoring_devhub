import logging
import os

from alert_monitoring.api.driven.atlassian_assets_repository.models.atlassian_assets_config import AtlassianAssetsConfig

logger = logging.getLogger(__name__)

WORKSPACE_ID_VAR = "ATLASSIAN_ASSETS_WORKSPACE_ID"
BASE_URL_VAR = "ATLASSIAN_ASSETS_BASE_URL"
EMAIL_VAR = "ATLASSIAN_ASSETS_EMAIL"
TOKEN_VAR = "ATLASSIAN_ASSETS_TOKEN"
OBJECT_TYPE_ID_VAR = "ATLASSIAN_ASSETS_OBJECT_TYPE_ID"
PAGE_SIZE_VAR = "ATLASSIAN_ASSETS_PAGE_SIZE"
MAX_PAGES_VAR = "ATLASSIAN_ASSETS_MAX_PAGES"
VERIFY_SSL_VAR = "ATLASSIAN_ASSETS_VERIFY_SSL"

DEFAULT_BASE_URL = "https://api.atlassian.com/jsm/assets"

_PROD_ENVS = {"pre", "pro"}


def _warn_insecure_ssl(verify_ssl: bool) -> None:
    env = os.environ.get("ENVIRONMENT", "").lower()
    if not verify_ssl and env in _PROD_ENVS:
        logger.warning("verify_ssl=False en entorno %s para Atlassian Assets; riesgo de seguridad.", env)


def load_atlassian_assets_config() -> AtlassianAssetsConfig | None:
    workspace_id = os.environ.get(WORKSPACE_ID_VAR)
    email = os.environ.get(EMAIL_VAR)
    token = os.environ.get(TOKEN_VAR)
    object_type_id = os.environ.get(OBJECT_TYPE_ID_VAR)

    if not workspace_id or not email or not token or not object_type_id:
        missing = [v for v, val in [
            (WORKSPACE_ID_VAR, workspace_id),
            (EMAIL_VAR, email),
            (TOKEN_VAR, token),
            (OBJECT_TYPE_ID_VAR, object_type_id),
        ] if not val]
        logger.warning("Variables de entorno de Atlassian Assets no definidas: %s; no se sincronizará el catálogo.", missing)
        return None

    verify_ssl = os.environ.get(VERIFY_SSL_VAR, "true").lower() != "false"
    _warn_insecure_ssl(verify_ssl)

    return AtlassianAssetsConfig(
        workspace_id=workspace_id,
        base_url=os.environ.get(BASE_URL_VAR, DEFAULT_BASE_URL),
        email=email,
        token=token,
        object_type_id=object_type_id,
        page_size=int(os.environ.get(PAGE_SIZE_VAR, "100")),
        max_pages=int(os.environ.get(MAX_PAGES_VAR, "200")),
        verify_ssl=verify_ssl,
    )
