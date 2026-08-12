from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List

from alert_monitoring.api.domain.models.alert import Alert
from alert_monitoring.api.domain.models.default_alert import DefaultAlert


@dataclass
class PrometheusSyncResult:
    total_rules: int
    adhoc_alerts: List[Alert] = field(default_factory=list)
    default_alerts: List[DefaultAlert] = field(default_factory=list)


class PrometheusAlertsProviderPort(ABC):

    @abstractmethod
    def fetch_alerts(self) -> PrometheusSyncResult:
        pass
