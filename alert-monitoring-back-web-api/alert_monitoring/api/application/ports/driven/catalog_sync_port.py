from abc import ABC, abstractmethod
from typing import List

from alert_monitoring.api.domain.models.catalog_app import CatalogApp


class CatalogSyncPort(ABC):

    @abstractmethod
    def fetch_catalog_apps(self) -> List[CatalogApp]:
        pass
