from unittest.mock import MagicMock

from alert_monitoring.api.driven.kibana_repository.adapters.kibana_adapter import KibanaAdapter
from alert_monitoring.api.driven.kibana_repository.models.kibana_config import KibanaConfig


def _config(name='k1') -> KibanaConfig:
    return KibanaConfig(name=name, base_url='http://kibana.example.com', api_key='key')


class TestKibanaAdapterFetchAlertApis:
    def test_aggregates_defaults_and_adhoc_across_configs(self, mocker):
        mapper = MagicMock()
        mapper.to_domain_split.side_effect = [
            (['default-1'], ['adhoc-1']),
            (['default-2'], ['adhoc-2']),
        ]
        adapter = KibanaAdapter(client=MagicMock(), mapper=mapper)
        mocker.patch.object(adapter, 'fetch_rules_by_config', return_value=[
            (_config('k1'), [{'name': 'rule-a'}]),
            (_config('k2'), [{'name': 'rule-b'}]),
        ])

        defaults, adhoc = adapter.fetch_alert_apis()

        assert defaults == ['default-1', 'default-2']
        assert adhoc == ['adhoc-1', 'adhoc-2']

    def test_no_configs_returns_empty_lists(self, mocker):
        mapper = MagicMock()
        adapter = KibanaAdapter(client=MagicMock(), mapper=mapper)
        mocker.patch.object(adapter, 'fetch_rules_by_config', return_value=[])

        defaults, adhoc = adapter.fetch_alert_apis()

        assert defaults == []
        assert adhoc == []
        mapper.to_domain_split.assert_not_called()
