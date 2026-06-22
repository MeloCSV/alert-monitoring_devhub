from typing import List, Optional
from logging import Logger

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse

from fwkpy_lib_core.common.injector import Injector
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup

from alert_monitoring.api.driving.api_rest.responses import ok_json
from alert_monitoring.api.driving.api_rest.models.blackout_response import BlackoutResponse, BlackoutMatcherResponse
from alert_monitoring.api.application.ports.driving.alert_service_port import AlertServicePort


router = APIRouter()

_ERROR_500 = {500: {'model': str}}


@router.post('/silences/sync', tags=['silences'], status_code=201, responses=_ERROR_500)
def sync_silences(
    alert_service: AlertServicePort = Depends(Injector.instance(AlertServicePort)),
    logger: Logger = Depends(Injector.instance(LoggerSetup, "LoggerSetup.get_logger")),
) -> JSONResponse:
    logger.info('sync_silences')
    synced = alert_service.sync_blackouts()
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"message": "Silencios sincronizados correctamente", "synced": synced},
    )


@router.get('/silences', tags=['silences'], response_model=List[BlackoutResponse], responses=_ERROR_500)
def get_silences(
    solution: Optional[str] = Query(None, description="Filtra los silencios por aplicación"),
    alert_service: AlertServicePort = Depends(Injector.instance(AlertServicePort)),
    logger: Logger = Depends(Injector.instance(LoggerSetup, "LoggerSetup.get_logger")),
) -> JSONResponse:
    logger.info('get_silences')
    blackouts = alert_service.get_active_blackouts(solution)
    payload = [
        BlackoutResponse(
            id=b.id,
            matchers=[BlackoutMatcherResponse(**m.model_dump()) for m in b.matchers],
            starts_at=b.starts_at,
            ends_at=b.ends_at,
            created_by=b.created_by,
            comment=b.comment,
            source=b.source,
        )
        for b in blackouts
    ]
    return ok_json(payload)
