from typing import List, Optional
from logging import Logger

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse

from fwkpy_lib_core.common.injector import Injector
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup

from alert_monitoring.api.driving.api_rest.responses import ok_json, ok_list
from alert_monitoring.api.driving.api_rest.models.alert_response import AlertResponse
from alert_monitoring.api.driving.api_rest.models.default_alert_response import DefaultAlertResponse
from alert_monitoring.api.driving.api_rest.models.solution_view_response import DefaultAlertViewResponse, SolutionViewResponse
from alert_monitoring.api.driving.api_rest.mappers.alert_dto_mapper import AlertDTOMapper
from alert_monitoring.api.application.ports.driving.alert_service_port import AlertServicePort
from alert_monitoring.api.domain.models.alert_filter import AlertFilter


router = APIRouter()

_ERROR_500 = {500: {'model': str}}


@router.post('/alert-app/sync/prometheus', tags=['alert-app'], status_code=201, responses=_ERROR_500)
def sync_prometheus_alerts(
    alert_service: AlertServicePort = Depends(Injector.instance(AlertServicePort)),
    logger: Logger = Depends(Injector.instance(LoggerSetup, "LoggerSetup.get_logger")),
) -> JSONResponse:
    logger.info('sync_prometheus_alerts')
    saved = alert_service.sync_prometheus_alerts()
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"message": "Alertas de Prometheus sincronizadas correctamente", "saved": saved},
    )


@router.post('/alert-app/sync/elastic', tags=['alert-app'], status_code=201, responses=_ERROR_500)
def sync_elastic_alerts(
    alert_service: AlertServicePort = Depends(Injector.instance(AlertServicePort)),
    logger: Logger = Depends(Injector.instance(LoggerSetup, "LoggerSetup.get_logger")),
) -> JSONResponse:
    logger.info('sync_elastic_alerts')
    saved = alert_service.sync_elastic_alerts()
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"message": "Alertas de Elastic sincronizadas correctamente", "saved": saved},
    )


@router.get('/alert-app', tags=['alert-app'], response_model=List[AlertResponse], responses=_ERROR_500)
def get_all_alerts(
    name: Optional[str] = Query(None, description="Filtra por nombre (coincidencia parcial)"),
    source_tool: Optional[str] = Query(None, description="Prometheus o Elastic"),
    severity: Optional[str] = Query(None, description="Warning, Critical o Principal"),
    environments: Optional[List[str]] = Query(None, description="Entornos: dev, itg, pre, pro"),
    solution: Optional[str] = Query(None, description="Filtra por solución (coincidencia exacta)"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de alertas a devolver"),
    offset: int = Query(0, ge=0, description="Número de alertas a omitir"),
    alert_service: AlertServicePort = Depends(Injector.instance(AlertServicePort)),
    api_rest_mapper: AlertDTOMapper = Depends(Injector.instance(AlertDTOMapper)),
    logger: Logger = Depends(Injector.instance(LoggerSetup, "LoggerSetup.get_logger")),
) -> JSONResponse:
    logger.info('get_all_alerts')
    filters = AlertFilter(
        name=name,
        source_tool=source_tool,
        severity=severity,
        environments=environments,
        solution=solution,
        limit=limit,
        offset=offset,
    )
    alerts = alert_service.get_all_alerts(filters)
    return ok_json(api_rest_mapper.to_models_decorator(alerts))


@router.get('/alert-app/defaults', tags=['alert-app'], response_model=List[DefaultAlertResponse], responses=_ERROR_500)
def get_default_alerts(
    alert_service: AlertServicePort = Depends(Injector.instance(AlertServicePort)),
    logger: Logger = Depends(Injector.instance(LoggerSetup, "LoggerSetup.get_logger")),
) -> JSONResponse:
    logger.info('get_default_alerts')
    defaults = alert_service.get_default_alerts()
    return ok_list(DefaultAlertResponse, defaults)


@router.get('/alert-app/overview/{app}', tags=['alert-app'], response_model=SolutionViewResponse, responses=_ERROR_500)
def get_alert_app_overview(
    app: str,
    alert_service: AlertServicePort = Depends(Injector.instance(AlertServicePort)),
    logger: Logger = Depends(Injector.instance(LoggerSetup, "LoggerSetup.get_logger")),
) -> JSONResponse:
    logger.info('get_alert_app_overview')
    view = alert_service.get_solution_view(app)
    payload = SolutionViewResponse(
        app=view.app,
        default_alerts=[DefaultAlertViewResponse(**d.model_dump()) for d in view.default_alerts],
        adhoc_alerts=[AlertResponse(**a.model_dump()) for a in view.adhoc_alerts],
        channels=view.channels,
    )
    return ok_json(payload)
