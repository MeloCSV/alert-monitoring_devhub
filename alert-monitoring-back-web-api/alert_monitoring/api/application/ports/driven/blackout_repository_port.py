from abc import ABC, abstractmethod
from typing import List

from alert_monitoring.api.domain.models.blackout import Blackout


class BlackoutRepositoryPort(ABC):

    @abstractmethod
    def upsert_batch(self, blackouts: List[Blackout]) -> None:
        pass

    @abstractmethod
    def get_all(self) -> List[Blackout]:
        pass
