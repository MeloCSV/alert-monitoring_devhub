from abc import ABC, abstractmethod
from typing import List

from alert_monitoring.api.domain.models.blackout import Blackout


class BlackoutProviderPort(ABC):

    @abstractmethod
    def fetch_active_blackouts(self) -> List[Blackout]:
        pass
