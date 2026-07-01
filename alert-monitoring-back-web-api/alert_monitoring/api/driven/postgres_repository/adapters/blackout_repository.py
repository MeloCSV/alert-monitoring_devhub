from typing import List, Optional

from fwkpy_lib_core.common.injector import inject
from fwkpy_lib_utils.common.observability.logger.logger_setup import LoggerSetup
from fwkpy_lib_database.synchronous.datasource import DataSourceManager

from alert_monitoring.api.domain.models.blackout import Blackout
from alert_monitoring.api.application.ports.driven.blackout_repository_port import BlackoutRepositoryPort
from alert_monitoring.api.driven.postgres_repository.models.blackout_model import BlackoutDB
from alert_monitoring.api.driven.postgres_repository.mappers.blackout_db_mapper import BlackoutDBMapper


class BlackoutRepositoryAdapter(BlackoutRepositoryPort):

    @inject(sqlalchemy_repository='DataSourceManager.get_scoped_session', logger="LoggerSetup.get_logger")
    def __init__(
        self,
        sqlalchemy_repository: DataSourceManager,
        blackout_db_mapper: BlackoutDBMapper,
        logger: LoggerSetup,
    ):
        self.sqlalchemy_repository = sqlalchemy_repository
        self.blackout_db_mapper = blackout_db_mapper
        self.logger = logger

    def upsert_batch(self, blackouts: List[Blackout], catalog_app_names: Optional[List[str]] = None) -> None:
        self.logger.info(f"Persistiendo {len(blackouts)} silencios")
        skipped = 0
        for blackout in blackouts:
            db_obj = self.blackout_db_mapper.to_db(blackout, catalog_app_names)
            existing = (
                self.sqlalchemy_repository.query(BlackoutDB)
                .filter(BlackoutDB.alertmanager_id == db_obj.alertmanager_id)
                .first()
            )
            if not db_obj.app_names:
                # los silencios se consultan por aplicación: si no matchea con
                # ninguna del catálogo no tiene sentido guardarlo (ni mantener
                # una fila antigua que ya haya dejado de matchear)
                if existing:
                    self.sqlalchemy_repository.delete(existing)
                skipped += 1
                continue
            if existing:
                existing.matchers = db_obj.matchers
                existing.starts_at = db_obj.starts_at
                existing.ends_at = db_obj.ends_at
                existing.created_by = db_obj.created_by
                existing.comment = db_obj.comment
                existing.state = db_obj.state
                existing.source = db_obj.source
                existing.app_names = db_obj.app_names
            else:
                self.sqlalchemy_repository.add(db_obj)
        self.sqlalchemy_repository.commit()
        if skipped:
            self.logger.info(f"Silencios omitidos por no matchear con ninguna app del catálogo: {skipped}")

    def get_all(self) -> List[Blackout]:
        self.logger.info("Consultando silencios activos")
        rows = (
            self.sqlalchemy_repository.query(BlackoutDB)
            .filter(BlackoutDB.state == "active")
            .all()
        )
        return self.blackout_db_mapper.to_domain_list(rows)
