import json
import logging
import os
from typing import List

from alert_monitoring.api.driven.alertmanager_repository.models.alertmanager_config import AlertManagerConfig

logger = logging.getLogger(__name__)

ENV_VAR = "ALERTMANAGERS"

_PROD_ENVS = {"pre", "pro"}


def _warn_insecure_ssl(name: str, verify_ssl: bool) -> None:
    env = os.environ.get("ENVIRONMENT", "").lower()
    if not verify_ssl and env in _PROD_ENVS:
        logger.warning("verify_ssl=False en entorno %s para AlertManager '%s'; riesgo de seguridad.", env, name)


def load_alertmanagers_from_env() -> List[AlertManagerConfig]:
    raw = os.environ.get(ENV_VAR)
    if not raw:
        logger.warning("Variable de entorno %s no definida; no se consultará ningún AlertManager.", ENV_VAR)
        return []

    try:
        items = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("No se puede parsear %s como JSON: %s", ENV_VAR, exc)
        return []

    if not isinstance(items, list):
        logger.error("%s debe ser una lista JSON de AlertManagers.", ENV_VAR)
        return []

    configs: List[AlertManagerConfig] = []
    for item in items:
        try:
            cfg = AlertManagerConfig(
                name=item["name"],
                url=item["url"],
                token=item.get("token"),
                verify_ssl=item.get("verify_ssl", True),
                host_header=item.get("host_header"),
                sni_hostname=item.get("sni_hostname"),
            )
            _warn_insecure_ssl(cfg.name, cfg.verify_ssl)
            configs.append(cfg)
        except KeyError as exc:
            logger.error("AlertManager mal configurado, falta el campo %s: %s", exc, item.get("name", "?"))
    return configs
