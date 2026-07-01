from datetime import datetime, timezone
from typing import List, Optional

from alert_monitoring.api.domain.models.blackout import Blackout, BlackoutMatcher
from alert_monitoring.api.driven.postgres_repository.models.blackout_model import BlackoutDB

_APP_MATCHER_FIELDS = frozenset({
    'namespace', 'solucion', 'solution', 'exported_namespace',
    'backend_target_name', 'deployment', 'replicaset', 'cronjob', 'pod',
})


class BlackoutDBMapper:

    def _parse_dt(self, value: str | datetime | None) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(value.replace('Z', '+00:00'))

    def _extract_app_name(self, blackout: Blackout, catalog_app_names: List[str]) -> Optional[str]:
        # nombres más largos primero para preferir el match más específico
        # (p.ej. "reservas-hoteles" antes que "reservas")
        candidates = sorted(catalog_app_names, key=len, reverse=True)
        for matcher in blackout.matchers:
            if matcher.name not in _APP_MATCHER_FIELDS or not matcher.is_equal or matcher.is_regex:
                continue
            value = matcher.value.lower()
            for name in candidates:
                lowered = name.lower()
                if value == lowered or value.startswith(f"{lowered}-") or value.startswith(f"{lowered}_"):
                    return name
        return None

    def to_db(self, blackout: Blackout, catalog_app_names: Optional[List[str]] = None) -> BlackoutDB:
        return BlackoutDB(
            alertmanager_id=blackout.id,
            matchers=[m.model_dump() for m in blackout.matchers],
            starts_at=self._parse_dt(blackout.starts_at),
            ends_at=self._parse_dt(blackout.ends_at),
            created_by=blackout.created_by,
            comment=blackout.comment,
            state=blackout.state,
            source=blackout.source,
            app_name=self._extract_app_name(blackout, catalog_app_names or []),
        )

    def to_domain(self, row: BlackoutDB) -> Blackout:
        return Blackout(
            id=row.alertmanager_id,
            matchers=[BlackoutMatcher(**m) for m in (row.matchers or [])],
            starts_at=row.starts_at,
            ends_at=row.ends_at,
            created_by=row.created_by,
            comment=row.comment,
            state=row.state,
            source=row.source,
        )

    def to_domain_list(self, rows: List[BlackoutDB]) -> List[Blackout]:
        return [self.to_domain(row) for row in rows]
