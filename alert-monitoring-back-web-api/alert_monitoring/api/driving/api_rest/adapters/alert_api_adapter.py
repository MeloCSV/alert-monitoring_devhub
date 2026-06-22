from logging import Logger
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse

from fwkpy_lib_core.common.injector import Injector
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup

from alert_monitoring.api.application.ports.driving.alert_api_service_port import AlertApiServicePort
from alert_monitoring.api.application.ports.driving.alert_service_port import AlertServicePort
from alert_monitoring.api.driving.api_rest.models.alert_api_response import AlertApiResponse
from alert_monitoring.api.driving.api_rest.models.api_solution_view_response import DefaultAlertApiViewResponse, ApiSolutionViewResponse
from alert_monitoring.api.driving.api_rest.responses import ok_json, ok_list


router = APIRouter()

_ERROR_500 = {500: {'model': str}}


@router.post('/alert-api/sync', tags=['alert-api'], status_code=201, responses=_ERROR_500)
def sync_alert_api_rules(
    service: AlertApiServicePort = Depends(Injector.instance(AlertApiServicePort)),
    logger: Logger = Depends(Injector.instance(LoggerSetup, "LoggerSetup.get_logger")),
) -> JSONResponse:
    logger.info('sync_alert_api_rules')
    saved = service.sync_alert_apis()
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"message": "Reglas de API sincronizadas correctamente", "saved": saved},
    )


@router.get('/alert-api/apis', tags=['alert-api'], response_model=List[str], responses=_ERROR_500)
def get_alert_api_apis(
    service: AlertApiServicePort = Depends(Injector.instance(AlertApiServicePort)),
    logger: Logger = Depends(Injector.instance(LoggerSetup, "LoggerSetup.get_logger")),
) -> JSONResponse:
    logger.info('get_alert_api_apis')
    return ok_json(service.get_apis())


@router.get('/alert-api', tags=['alert-api'], response_model=List[AlertApiResponse], responses=_ERROR_500)
def get_alert_api_rules(
    api: Optional[str] = Query(None, description="Filtra las reglas por API"),
    service: AlertApiServicePort = Depends(Injector.instance(AlertApiServicePort)),
    logger: Logger = Depends(Injector.instance(LoggerSetup, "LoggerSetup.get_logger")),
) -> JSONResponse:
    logger.info(f'get_alert_api_rules api={api}')
    rules = service.get_alert_apis(api=api)
    return ok_list(AlertApiResponse, rules)


@router.get('/alert-api/overview/{app}', tags=['alert-api'], response_model=ApiSolutionViewResponse, responses=_ERROR_500)
def get_alert_api_overview(
    app: str,
    alert_service: AlertServicePort = Depends(Injector.instance(AlertServicePort)),
    logger: Logger = Depends(Injector.instance(LoggerSetup, "LoggerSetup.get_logger")),
) -> JSONResponse:
    logger.info('get_alert_api_overview')
    view = alert_service.get_api_solution_view(app)
    payload = ApiSolutionViewResponse(
        app=view.app,
        default_alerts=[DefaultAlertApiViewResponse(**d.model_dump()) for d in view.default_alerts],
        adhoc_alerts=[AlertApiResponse(**a.model_dump()) for a in view.adhoc_alerts],
        api_microservice_map=view.api_microservice_map,
        channels=view.channels,
    )
    return ok_json(payload)
