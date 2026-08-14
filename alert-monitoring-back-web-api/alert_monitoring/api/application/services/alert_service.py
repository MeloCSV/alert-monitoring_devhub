import re
import threading
import time
from typing import Any, Callable, Dict, List, Optional, TypeVar

_T = TypeVar("_T")
_CACHE_TTL_SECS = 300  # 5 minutes


class _TTLCache:
    """Thread-safe single-value cache with a fixed TTL."""

    def __init__(self, ttl: float = _CACHE_TTL_SECS) -> None:
        self._ttl = ttl
        self._value: Any = None
        self._expires_at: float = 0.0
        self._lock = threading.Lock()

    def get_or_compute(self, fn: Callable[[], _T]) -> _T:
        with self._lock:
            if time.monotonic() < self._expires_at:
                return self._value
            self._value = fn()
            self._expires_at = time.monotonic() + self._ttl
            return self._value

    def invalidate(self) -> None:
        with self._lock:
            self._expires_at = 0.0

from fwkpy_lib_core.common.injector import inject
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup

from alert_monitoring.api.application.ports.driving.alert_service_port import AlertServicePort
from alert_monitoring.api.application.ports.driven.alert_repository_port import AlertRepositoryPort
from alert_monitoring.api.application.ports.driven.catalog_app_api_repository_port import CatalogAppApiRepositoryPort
from alert_monitoring.api.application.ports.driven.catalog_app_repository_port import CatalogAppRepositoryPort
from alert_monitoring.api.application.ports.driven.default_alert_api_repository_port import DefaultAlertApiRepositoryPort
from alert_monitoring.api.application.ports.driven.default_alert_repository_port import DefaultAlertRepositoryPort
from alert_monitoring.api.application.ports.driven.alert_api_repository_port import AlertApiRepositoryPort
from alert_monitoring.api.application.ports.driven.blackout_repository_port import BlackoutRepositoryPort
from alert_monitoring.api.application.ports.driven.blackout_provider_port import BlackoutProviderPort
from alert_monitoring.api.application.ports.driven.elastic_alerts_provider_port import ElasticAlertsProviderPort
from alert_monitoring.api.application.ports.driven.prometheus_alerts_provider_port import PrometheusAlertsProviderPort
from alert_monitoring.api.application.exceptions.solution_not_found import SolutionNotFoundException
from alert_monitoring.api.application.use_cases.get_all_alerts_use_case import GetAllAlertsUseCase
from alert_monitoring.api.application.use_cases.get_api_solution_view_use_case import GetApiSolutionViewUseCase
from alert_monitoring.api.application.use_cases.get_solution_view_use_case import GetSolutionViewUseCase
from alert_monitoring.api.application.use_cases.save_alerts_use_case import SaveAlertsUseCase
from alert_monitoring.api.application.services.catalog_lookup import build_catalog_lookup
from alert_monitoring.api.domain.models.alert import Alert
from alert_monitoring.api.domain.models.alert_filter import AlertFilter
from alert_monitoring.api.domain.models.blackout import Blackout
from alert_monitoring.api.domain.models.default_alert import DefaultAlert
from alert_monitoring.api.domain.models.solution_view import SolutionView
from alert_monitoring.api.domain.models.api_solution_view import ApiSolutionView


class AlertService(AlertServicePort):

    @inject(logger="LoggerSetup.get_logger")
    def __init__(
        self,
        alert_repository: AlertRepositoryPort,
        alert_api_repository: AlertApiRepositoryPort,
        catalog_app_repository: CatalogAppRepositoryPort,
        catalog_app_api_repository: CatalogAppApiRepositoryPort,
        default_alert_repository: DefaultAlertRepositoryPort,
        default_alert_api_repository: DefaultAlertApiRepositoryPort,
        blackout_repository: BlackoutRepositoryPort,
        prometheus_provider: PrometheusAlertsProviderPort,
        elastic_provider: ElasticAlertsProviderPort,
        blackout_provider: BlackoutProviderPort,
        logger: LoggerSetup,
    ):
        self.alert_repository = alert_repository
        self.alert_api_repository = alert_api_repository
        self.catalog_app_repository = catalog_app_repository
        self.catalog_app_api_repository = catalog_app_api_repository
        self.default_alert_repository = default_alert_repository
        self.default_alert_api_repository = default_alert_api_repository
        self.blackout_repository = blackout_repository
        self.save_use_case = SaveAlertsUseCase(alert_repository)
        self.get_all_use_case = GetAllAlertsUseCase(alert_repository)
        self.get_solution_view_use_case = GetSolutionViewUseCase(
            alert_repository, default_alert_repository
        )
        self.get_api_solution_view_use_case = GetApiSolutionViewUseCase(
            catalog_app_api_repository, default_alert_api_repository, alert_api_repository
        )
        self.prometheus_provider = prometheus_provider
        self.elastic_provider = elastic_provider
        self.blackout_provider = blackout_provider
        self.logger = logger
        self._catalog_lookup_cache: _TTLCache = _TTLCache()
        self._default_alerts_cache: _TTLCache = _TTLCache()

    def _build_catalog_lookup(self) -> Dict[str, str]:
        return build_catalog_lookup(self.catalog_app_repository)

    def _normalize_solutions(self, alerts: List[Alert], catalog_lookup: Dict[str, str]) -> List[Alert]:
        # las alertas se consultan por aplicación: sin una solución reconocida
        # en el catálogo no tiene sentido guardarlas
        normalized: List[Alert] = []
        for alert in alerts:
            if not alert.solution:
                continue
            canonical = catalog_lookup.get(alert.solution.lower())
            if not canonical:
                self.logger.warning(f"solution '{alert.solution}' not found in catalog")
                continue
            alert.solution = canonical
            normalized.append(alert)
        return normalized

    def sync_prometheus_alerts(self) -> int:
        self.logger.info('sync_prometheus_alerts')
        result = self.prometheus_provider.fetch_alerts()
        catalog_lookup = self._catalog_lookup_cache.get_or_compute(self._build_catalog_lookup)
        adhoc_alerts = self._normalize_solutions(result.adhoc_alerts, catalog_lookup)

        self.alert_repository.delete_by_source_tool("Prometheus")
        self.save_use_case.execute(adhoc_alerts)
        if result.default_alerts:
            self.default_alert_repository.upsert_batch(result.default_alerts)
        self._default_alerts_cache.invalidate()
        return result.total_rules

    def sync_elastic_alerts(self) -> int:
        self.logger.info('sync_elastic_alerts')
        alerts = self.elastic_provider.fetch_alerts()
        catalog_lookup = self._catalog_lookup_cache.get_or_compute(self._build_catalog_lookup)
        alerts = self._normalize_solutions(alerts, catalog_lookup)
        self.alert_repository.delete_by_source_tool("Elastic")
        self.save_use_case.execute(alerts)
        return len(alerts)

    def get_all_alerts(self, filters: Optional[AlertFilter] = None) -> List[Alert]:
        self.logger.info('get_all_alerts')
        return self.get_all_use_case.execute(filters)

    _APP_MATCHER_FIELDS = frozenset({
        'namespace', 'solucion', 'solution', 'exported_namespace',
        'backend_target_name', 'deployment', 'replicaset', 'cronjob', 'pod',
    })

    def _blackout_matches_solution(self, blackout: Blackout, solution: str) -> bool:
        sol = solution.lower()
        variants = {sol, f"{sol}-back", f"{sol}-front"}
        for matcher in blackout.matchers:
            if matcher.name not in self._APP_MATCHER_FIELDS or not matcher.is_equal:
                continue
            if matcher.is_regex:
                try:
                    pattern = re.compile(matcher.value, re.IGNORECASE)
                    if any(pattern.search(v) for v in variants):
                        return True
                except re.error:
                    continue
            else:
                val = matcher.value.lower()
                if val in variants or any(val.startswith(f"{v}-") for v in variants):
                    return True
        return False

    def sync_blackouts(self) -> int:
        self.logger.info('sync_blackouts')
        blackouts = self.blackout_provider.fetch_active_blackouts()
        if blackouts:
            catalog_app_names = [app.name for app in self.catalog_app_repository.get_all()]
            self.blackout_repository.upsert_batch(blackouts, catalog_app_names)
        self.logger.info(f'sync_blackouts: {len(blackouts)} silencios persistidos')
        return len(blackouts)

    def get_active_blackouts(self, solution: Optional[str] = None) -> List[Blackout]:
        self.logger.info(f'get_active_blackouts solution={solution}')
        blackouts = self.blackout_repository.get_all()
        if solution:
            blackouts = [b for b in blackouts if self._blackout_matches_solution(b, solution)]
        return blackouts

    def get_default_alerts(self) -> List[DefaultAlert]:
        self.logger.info('get_default_alerts')
        return self._default_alerts_cache.get_or_compute(self.default_alert_repository.get_all)

    def get_solution_view(self, solution: str) -> SolutionView:
        self.logger.info(f'get_solution_view solution={solution}')
        catalog_lookup = self._catalog_lookup_cache.get_or_compute(self._build_catalog_lookup)
        if solution.lower() not in catalog_lookup:
            raise SolutionNotFoundException(solution)
        return self.get_solution_view_use_case.execute(solution)

    def get_api_solution_view(self, app: str) -> ApiSolutionView:
        self.logger.info(f'get_api_solution_view app={app}')
        catalog_lookup = self._catalog_lookup_cache.get_or_compute(self._build_catalog_lookup)
        if app.lower() not in catalog_lookup:
            raise SolutionNotFoundException(app)
        return self.get_api_solution_view_use_case.execute(app)
