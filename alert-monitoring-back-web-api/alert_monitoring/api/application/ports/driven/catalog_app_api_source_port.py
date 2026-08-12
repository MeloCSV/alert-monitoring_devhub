from abc import ABC, abstractmethod
from typing import List


class CatalogAppApiSourcePort(ABC):

    @abstractmethod
    def fetch_entries(self) -> List[dict]:
        pass
