from unittest.mock import MagicMock

from alert_monitoring.api.driven.prometheus_repository.adapters.prometheus_adapter import PrometheusAdapter


class TestPrometheusAdapterFetchAlerts:
    def test_builds_sync_result_from_mapper(self, mocker):
        rules = [MagicMock(), MagicMock(), MagicMock()]
        mapper = MagicMock()
        mapper.to_adhoc_alerts.return_value = ['adhoc-alert']
        mapper.to_default_alerts.return_value = ['default-alert']
        adapter = PrometheusAdapter(client=MagicMock(), mapper=mapper)
        mocker.patch.object(adapter, 'fetch_rules', return_value=rules)

        result = adapter.fetch_alerts()

        assert result.total_rules == 3
        assert result.adhoc_alerts == ['adhoc-alert']
        assert result.default_alerts == ['default-alert']
        mapper.to_adhoc_alerts.assert_called_once_with(rules)
        mapper.to_default_alerts.assert_called_once_with(rules)

    def test_empty_rules_produce_empty_result(self, mocker):
        mapper = MagicMock()
        mapper.to_adhoc_alerts.return_value = []
        mapper.to_default_alerts.return_value = []
        adapter = PrometheusAdapter(client=MagicMock(), mapper=mapper)
        mocker.patch.object(adapter, 'fetch_rules', return_value=[])

        result = adapter.fetch_alerts()

        assert result.total_rules == 0
        assert result.adhoc_alerts == []
        assert result.default_alerts == []
