from abc import ABC, abstractmethod
from typing import List, Tuple

from alert_monitoring.api.domain.models.alert_api import AlertApi
from alert_monitoring.api.domain.models.default_alert_api import DefaultAlertApi


class AlertApiSyncPort(ABC):

    @abstractmethod
    def fetch_alert_apis(self) -> Tuple[List[DefaultAlertApi], List[AlertApi]]:
        pass
