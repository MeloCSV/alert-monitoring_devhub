import logging
from typing import List, Optional, Tuple

from alert_monitoring.api.application.ports.driven.alert_api_sync_port import AlertApiSyncPort
from alert_monitoring.api.domain.models.alert_api import AlertApi
from alert_monitoring.api.domain.models.default_alert_api import DefaultAlertApi
from alert_monitoring.api.driven.kibana_repository.clients.kibana_http_client import KibanaHttpClient
from alert_monitoring.api.driven.kibana_repository.config.kibana_settings import (
    load_kibana_elastic_from_env,
    load_kibana_elastic_gcp_from_env,
)
from alert_monitoring.api.driven.kibana_repository.mappers.kibana_rule_mapper import KibanaRuleMapper
from alert_monitoring.api.driven.kibana_repository.models.kibana_config import KibanaConfig

logger = logging.getLogger(__name__)


class KibanaAdapter(AlertApiSyncPort):

    def __init__(
        self,
        client: Optional[KibanaHttpClient] = None,
        mapper: Optional[KibanaRuleMapper] = None,
    ) -> None:
        self.client = client or KibanaHttpClient()
        self.mapper = mapper or KibanaRuleMapper()

    def fetch_alert_apis(self) -> Tuple[List[DefaultAlertApi], List[AlertApi]]:
        default_alerts: List[DefaultAlertApi] = []
        adhoc_alerts: List[AlertApi] = []
        for config, raw_rules in self.fetch_rules_by_config():
            defaults, adhoc = self.mapper.to_domain_split(raw_rules, config)
            default_alerts.extend(defaults)
            adhoc_alerts.extend(adhoc)
        return default_alerts, adhoc_alerts

    def fetch_rules(self, configs: Optional[List[KibanaConfig]] = None) -> List[dict]:
        configs = configs if configs is not None else load_kibana_elastic_gcp_from_env()
        if not configs:
            return []

        rules: List[dict] = []
        for config in configs:
            logger.info("Recogiendo reglas de alerting de Kibana %s", config.name)
            rules.extend(self.client.fetch_rules(config))
        return rules

    def fetch_rules_by_config(
        self, configs: Optional[List[KibanaConfig]] = None
    ) -> List[Tuple[KibanaConfig, List[dict]]]:
        configs = configs if configs is not None else load_kibana_elastic_from_env()
        if not configs:
            return []

        result: List[Tuple[KibanaConfig, List[dict]]] = []
        for config in configs:
            logger.info("Recogiendo reglas de alerting de Kibana %s", config.name)
            result.append((config, self.client.fetch_rules(config)))
        return result
