import re
from datetime import datetime, timezone
from typing import List, Optional

from alert_monitoring.api.domain.models.blackout import Blackout, BlackoutMatcher
from alert_monitoring.api.driven.postgres_repository.models.blackout_model import BlackoutDB

_APP_MATCHER_FIELDS = frozenset({
    'namespace', 'solucion', 'solution', 'exported_namespace',
    'backend_target_name', 'deployment', 'replicaset', 'cronjob', 'pod',
    'alertname',
})


class BlackoutDBMapper:

    def _parse_dt(self, value: str | datetime | None) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(value.replace('Z', '+00:00'))

    def _extract_app_names(self, blackout: Blackout, catalog_app_names: List[str]) -> List[str]:
        # nombres más largos primero para preferir el match más específico
        # (p.ej. "reservas-hoteles" antes que "reservas") cuando se solapan
        candidates = sorted(catalog_app_names, key=len, reverse=True)
        found: List[str] = []
        for matcher in blackout.matchers:
            if matcher.name not in _APP_MATCHER_FIELDS or not matcher.is_equal:
                continue
            value = self._normalize(matcher.value)
            # un mismo matcher puede listar varias apps distintas (p.ej. una regex
            # con alternancia "organigrama.*|labmng.*"), así que hay que detectar
            # todas las que aparezcan, no solo la primera
            consumed_spans: List[tuple[int, int]] = []
            for name in candidates:
                lowered = re.escape(self._normalize(name))
                # el nombre de catálogo debe aparecer delimitado por separadores
                # no alfanuméricos (o inicio/fin), tanto en valores exactos como
                # en patrones regex tipo ".*reservas-back.*"
                for match in re.finditer(rf"(?<![a-z0-9]){lowered}(?![a-z0-9])", value):
                    start, end = match.span()
                    if any(start < e and s < end for s, e in consumed_spans):
                        continue  # ya cubierto por un nombre de catálogo más específico
                    consumed_spans.append((start, end))
                    if name not in found:
                        found.append(name)
        return found

    # solo letra minúscula -> mayúscula cuenta como límite; un dígito antes de una
    # mayúscula ("P1Secos") no separa, porque suele ser parte del mismo código de app
    _CAMEL_BOUNDARY = re.compile(r'(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])')

    @classmethod
    def _normalize(cls, value: str) -> str:
        # inserta un separador en los límites camelCase antes de pasar a minúsculas,
        # tanto en transiciones simples ("p1secosAlert" -> "p1secos-alert") como en
        # acrónimos seguidos de palabra ("CloudSQLNotAvailable" -> "cloud-sql-not-available")
        return cls._CAMEL_BOUNDARY.sub('-', value).lower()

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
            app_names=self._extract_app_names(blackout, catalog_app_names or []),
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
