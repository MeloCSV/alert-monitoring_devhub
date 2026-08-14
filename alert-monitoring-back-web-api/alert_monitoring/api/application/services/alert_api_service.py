from typing import List, Optional

from fwkpy_lib_core.common.injector import inject
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup

from alert_monitoring.api.application.ports.driven.alert_api_repository_port import AlertApiRepositoryPort
from alert_monitoring.api.application.ports.driven.alert_api_sync_port import AlertApiSyncPort
from alert_monitoring.api.application.ports.driven.default_alert_api_repository_port import DefaultAlertApiRepositoryPort
from alert_monitoring.api.application.ports.driving.alert_api_service_port import AlertApiServicePort
from alert_monitoring.api.domain.models.alert_api import AlertApi


class AlertApiService(AlertApiServicePort):

    @inject(logger="LoggerSetup.get_logger")
    def __init__(
        self,
        alert_api_repository: AlertApiRepositoryPort,
        default_alert_api_repository: DefaultAlertApiRepositoryPort,
        alert_api_provider: AlertApiSyncPort,
        logger: LoggerSetup,
    ):
        self.alert_api_repository = alert_api_repository
        self.default_alert_api_repository = default_alert_api_repository
        self.alert_api_provider = alert_api_provider
        self.logger = logger

    def sync_alert_apis(self) -> int:
        self.logger.info("sync_alert_apis")
        default_alerts, adhoc_rules = self.alert_api_provider.fetch_alert_apis()

        self.default_alert_api_repository.upsert_batch(default_alerts)
        self.default_alert_api_repository.delete_where_not_in([d.raw_name for d in default_alerts])
        self.alert_api_repository.delete_all()
        self.alert_api_repository.save_all(adhoc_rules)

        self.logger.info(
            f"sync_alert_apis: {len(default_alerts)} reglas globales en default_alert_api, "
            f"{len(adhoc_rules)} reglas ad-hoc en alert_api"
        )
        return len(default_alerts) + len(adhoc_rules)

    def get_alert_apis(self, api: Optional[str] = None) -> List[AlertApi]:
        self.logger.info(f"get_alert_apis api={api}")
        return self.alert_api_repository.get_all(api=api)

    def get_apis(self) -> List[str]:
        self.logger.info("get_apis")
        return self.alert_api_repository.get_distinct_apis()
