import pytest
from unittest.mock import MagicMock

from alert_monitoring.api.domain.models.blackout import Blackout, BlackoutMatcher
from alert_monitoring.api.driven.postgres_repository.adapters.blackout_repository import BlackoutRepositoryAdapter
from alert_monitoring.api.driven.postgres_repository.mappers.blackout_db_mapper import BlackoutDBMapper
from alert_monitoring.api.driven.postgres_repository.models.blackout_model import BlackoutDB


def _make_blackout(
    id: str = "am-id-1",
    matchers: list | None = None,
    state: str = "active",
    source: str = "alertmanager-prod",
    comment: str = "Silencio de prueba",
) -> Blackout:
    return Blackout(
        id=id,
        matchers=matchers or [BlackoutMatcher(name="namespace", value="my-app", is_regex=False, is_equal=True)],
        starts_at="2026-01-01T00:00:00Z",
        ends_at="2026-12-31T23:59:59Z",
        created_by="tester",
        comment=comment,
        state=state,
        source=source,
    )


@pytest.mark.integration
class TestBlackoutRepositoryIntegration:

    @pytest.fixture
    def repo(self, db_session):
        return BlackoutRepositoryAdapter(
            sqlalchemy_repository=db_session,
            blackout_db_mapper=BlackoutDBMapper(),
            logger=MagicMock(),
        )

    def test_upsert_batch_inserts_new_blackouts(self, repo, db_session):
        """upsert_batch inserta silencios nuevos en la base de datos."""
        blackouts = [_make_blackout("id-1"), _make_blackout("id-2")]

        repo.upsert_batch(blackouts)

        rows = db_session.query(BlackoutDB).all()
        assert len(rows) == 2
        assert {r.alertmanager_id for r in rows} == {"id-1", "id-2"}

    def test_upsert_batch_updates_existing_blackout(self, repo, db_session):
        """upsert_batch actualiza un silencio existente sin duplicarlo."""
        repo.upsert_batch([_make_blackout("id-1", comment="original")])
        repo.upsert_batch([_make_blackout("id-1", comment="updated")])

        rows = db_session.query(BlackoutDB).all()
        assert len(rows) == 1
        assert rows[0].comment == "updated"

    def test_upsert_batch_persists_all_fields(self, repo, db_session):
        """Todos los campos del silencio se almacenan correctamente."""
        matchers = [
            BlackoutMatcher(name="namespace", value="my-app", is_regex=False, is_equal=True),
            BlackoutMatcher(name="severity", value="critical", is_regex=False, is_equal=True),
        ]
        blackout = _make_blackout("id-full", matchers=matchers, state="active", source="am-prod", comment="full fields")

        repo.upsert_batch([blackout])

        row = db_session.query(BlackoutDB).filter_by(alertmanager_id="id-full").first()
        assert row is not None
        assert row.state == "active"
        assert row.source == "am-prod"
        assert row.comment == "full fields"
        assert row.created_by == "tester"
        assert row.starts_at == "2026-01-01T00:00:00Z"
        assert row.ends_at == "2026-12-31T23:59:59Z"
        assert len(row.matchers) == 2
        assert row.matchers[0]["name"] == "namespace"

    def test_upsert_batch_extracts_app_names_matching_catalog_exactly(self, repo, db_session):
        """app_names incluye la app cuando el matcher coincide exactamente con el catálogo."""
        blackout = _make_blackout(
            "id-app",
            matchers=[BlackoutMatcher(name="namespace", value="mi-servicio", is_regex=False, is_equal=True)],
        )

        repo.upsert_batch([blackout], catalog_app_names=["mi-servicio"])

        row = db_session.query(BlackoutDB).filter_by(alertmanager_id="id-app").first()
        assert row.app_names == ["mi-servicio"]

    def test_upsert_batch_extracts_app_names_matching_catalog_prefix(self, repo, db_session):
        """app_names incluye la app cuando el matcher es la app del catálogo con un sufijo (p.ej. '-back')."""
        blackout = _make_blackout(
            "id-app-prefix",
            matchers=[BlackoutMatcher(name="namespace", value="reservas-back", is_regex=False, is_equal=True)],
        )

        repo.upsert_batch([blackout], catalog_app_names=["reservas"])

        row = db_session.query(BlackoutDB).filter_by(alertmanager_id="id-app-prefix").first()
        assert row.app_names == ["reservas"]

    def test_upsert_batch_extracts_app_names_from_regex_matcher(self, repo, db_session):
        """app_names incluye la app aunque el matcher sea una regex de Alertmanager (p.ej. '.*reservas-back.*')."""
        blackout = _make_blackout(
            "id-app-regex",
            matchers=[BlackoutMatcher(name="backend_target_name", value=".*reservas-back.*", is_regex=True, is_equal=True)],
        )

        repo.upsert_batch([blackout], catalog_app_names=["reservas"])

        row = db_session.query(BlackoutDB).filter_by(alertmanager_id="id-app-regex").first()
        assert row.app_names == ["reservas"]

    def test_upsert_batch_extracts_app_names_from_alertname_camel_case(self, repo, db_session):
        """app_names se calcula a partir del alertname aunque use camelCase (p.ej. 'P1SecosAlert')."""
        blackout = _make_blackout(
            "id-app-camel",
            matchers=[BlackoutMatcher(name="alertname", value="P1SecosAlert", is_regex=False, is_equal=True)],
        )

        repo.upsert_batch([blackout], catalog_app_names=["p1secos"])

        row = db_session.query(BlackoutDB).filter_by(alertmanager_id="id-app-camel").first()
        assert row.app_names == ["p1secos"]

    def test_upsert_batch_extracts_app_names_from_alertname_snake_case(self, repo, db_session):
        """app_names se calcula a partir del alertname con snake_case (p.ej. 'p1secos_alert')."""
        blackout = _make_blackout(
            "id-app-snake",
            matchers=[BlackoutMatcher(name="alertname", value="p1secos_alert", is_regex=False, is_equal=True)],
        )

        repo.upsert_batch([blackout], catalog_app_names=["p1secos"])

        row = db_session.query(BlackoutDB).filter_by(alertmanager_id="id-app-snake").first()
        assert row.app_names == ["p1secos"]

    def test_upsert_batch_extracts_multiple_app_names(self, repo, db_session):
        """app_names incluye varias apps cuando distintos matchers del mismo silencio apuntan a apps distintas."""
        blackout = _make_blackout(
            "id-app-multi",
            matchers=[
                BlackoutMatcher(name="namespace", value="reservas-back", is_regex=False, is_equal=True),
                BlackoutMatcher(name="deployment", value="hoteles-front", is_regex=False, is_equal=True),
            ],
        )

        repo.upsert_batch([blackout], catalog_app_names=["reservas", "hoteles"])

        row = db_session.query(BlackoutDB).filter_by(alertmanager_id="id-app-multi").first()
        assert row.app_names == ["reservas", "hoteles"]

    def test_upsert_batch_extracts_multiple_app_names_from_single_regex_alternation(self, repo, db_session):
        """app_names incluye varias apps cuando UN SOLO matcher regex las lista por alternancia (p.ej. 'a|b')."""
        blackout = _make_blackout(
            "id-app-alternation",
            matchers=[BlackoutMatcher(name="alertname", value=".*organigrama.*|.*labmng.*", is_regex=True, is_equal=True)],
        )

        repo.upsert_batch([blackout], catalog_app_names=["organigrama", "labmng"])

        row = db_session.query(BlackoutDB).filter_by(alertmanager_id="id-app-alternation").first()
        assert row.app_names == ["organigrama", "labmng"]

    def test_upsert_batch_app_names_empty_when_no_catalog_match(self, repo, db_session):
        """app_names queda vacío si el valor del matcher no coincide con ninguna app del catálogo."""
        blackout = _make_blackout(
            "id-app-nomatch",
            matchers=[BlackoutMatcher(name="namespace", value="algo-desconocido", is_regex=False, is_equal=True)],
        )

        repo.upsert_batch([blackout], catalog_app_names=["reservas", "mi-servicio"])

        row = db_session.query(BlackoutDB).filter_by(alertmanager_id="id-app-nomatch").first()
        assert row.app_names == []

    def test_upsert_batch_empty_list_does_nothing(self, repo, db_session):
        """upsert_batch con lista vacía no inserta ninguna fila."""
        repo.upsert_batch([])

        rows = db_session.query(BlackoutDB).all()
        assert rows == []

    def test_upsert_batch_mixed_insert_and_update(self, repo, db_session):
        """upsert_batch maneja correctamente una mezcla de inserts y updates."""
        repo.upsert_batch([_make_blackout("id-existing", comment="old")])

        repo.upsert_batch([
            _make_blackout("id-existing", comment="new"),
            _make_blackout("id-new"),
        ])

        rows = db_session.query(BlackoutDB).all()
        assert len(rows) == 2
        existing = next(r for r in rows if r.alertmanager_id == "id-existing")
        assert existing.comment == "new"

    def test_get_all_returns_active_blackouts(self, repo):
        """get_all devuelve solo los silencios con state='active'."""
        repo.upsert_batch([
            _make_blackout("id-active", state="active"),
            _make_blackout("id-expired", state="expired"),
        ])

        result = repo.get_all()

        assert len(result) == 1
        assert result[0].id == "id-active"

    def test_get_all_maps_domain_fields(self, repo):
        """get_all devuelve objetos Blackout con todos los campos correctos."""
        repo.upsert_batch([_make_blackout("id-full")])

        result = repo.get_all()

        assert len(result) == 1
        b = result[0]
        assert b.id == "id-full"
        assert b.state == "active"
        assert b.source == "alertmanager-prod"
        assert b.comment == "Silencio de prueba"
        assert b.created_by == "tester"
        assert len(b.matchers) == 1
        assert b.matchers[0].name == "namespace"
        assert b.matchers[0].value == "my-app"

    def test_get_all_empty_when_no_blackouts(self, repo):
        """get_all devuelve lista vacía si no hay silencios."""
        result = repo.get_all()

        assert result == []
