from typing import List

from alert_monitoring.api.application.ports.driven.catalog_sync_port import CatalogSyncPort
from alert_monitoring.api.domain.models.catalog_app import CatalogApp


class DevhubCatalogAdapter(CatalogSyncPort):

    def fetch_catalog_apps(self) -> List[CatalogApp]:
        # Aquí vendrá la llamada a base de datos para conseguir el nombre de la aplicación y el código CSW
        return []
