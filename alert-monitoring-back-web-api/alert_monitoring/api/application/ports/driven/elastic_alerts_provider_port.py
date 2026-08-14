from abc import ABC, abstractmethod
from typing import List

from alert_monitoring.api.domain.models.alert import Alert


class ElasticAlertsProviderPort(ABC):

    @abstractmethod
    def fetch_alerts(self) -> List[Alert]:
        pass
