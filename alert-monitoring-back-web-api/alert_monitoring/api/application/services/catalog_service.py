from typing import List, Optional

from fwkpy_lib_core.common.injector import inject
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup

from alert_monitoring.api.application.ports.driving.catalog_service_port import CatalogServicePort
from alert_monitoring.api.application.ports.driven.catalog_app_repository_port import CatalogAppRepositoryPort
from alert_monitoring.api.application.ports.driven.catalog_sync_port import CatalogSyncPort
from alert_monitoring.api.domain.models.catalog_app import CatalogApp


class CatalogService(CatalogServicePort):

    @inject(logger="LoggerSetup.get_logger")
    def __init__(
        self,
        catalog_app_repository: CatalogAppRepositoryPort,
        catalog_sync: CatalogSyncPort,
        logger: LoggerSetup,
    ):
        self.catalog_app_repository = catalog_app_repository
        self.catalog_sync = catalog_sync
        self.logger = logger

    def sync_catalog(self) -> int:
        self.logger.info("sync_catalog")
        apps = self.catalog_sync.fetch_catalog_apps()
        self.catalog_app_repository.save_all(apps)
        return len(apps)

    def get_all_catalog_apps(self, name: Optional[str] = None) -> List[CatalogApp]:
        self.logger.info(f"get_all_catalog_apps name={name}")
        return self.catalog_app_repository.get_all(name=name)
