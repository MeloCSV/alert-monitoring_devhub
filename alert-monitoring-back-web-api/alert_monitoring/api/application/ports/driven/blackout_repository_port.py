from abc import ABC, abstractmethod
from typing import List, Optional

from alert_monitoring.api.domain.models.blackout import Blackout


class BlackoutRepositoryPort(ABC):

    @abstractmethod
    def upsert_batch(self, blackouts: List[Blackout], catalog_app_names: Optional[List[str]] = None) -> None:
        pass

    @abstractmethod
    def get_all(self) -> List[Blackout]:
        pass
