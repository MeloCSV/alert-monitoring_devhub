from typing import List

from alert_monitoring.api.domain.models.blackout import Blackout, BlackoutMatcher
from alert_monitoring.api.driven.postgres_repository.models.blackout_model import BlackoutDB

_APP_MATCHER_FIELDS = frozenset({
    'namespace', 'solucion', 'solution', 'exported_namespace',
    'backend_target_name', 'deployment', 'replicaset', 'cronjob', 'pod',
})


class BlackoutDBMapper:

    def _extract_app_name(self, blackout: Blackout) -> str | None:
        for matcher in blackout.matchers:
            if matcher.name in _APP_MATCHER_FIELDS and matcher.is_equal and not matcher.is_regex:
                return matcher.value
        return None

    def to_db(self, blackout: Blackout) -> BlackoutDB:
        return BlackoutDB(
            alertmanager_id=blackout.id,
            matchers=[m.model_dump() for m in blackout.matchers],
            starts_at=blackout.starts_at,
            ends_at=blackout.ends_at,
            created_by=blackout.created_by,
            comment=blackout.comment,
            state=blackout.state,
            source=blackout.source,
            app_name=self._extract_app_name(blackout),
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
