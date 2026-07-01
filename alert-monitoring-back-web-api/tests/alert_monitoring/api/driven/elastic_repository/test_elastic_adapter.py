from alert_monitoring.api.driven.elastic_repository.adapters.elastic_adapter import ElasticAdapter


def _make_item(**kwargs) -> dict:
    defaults = dict(
        id='rule-1',
        name='My Rule',
        enabled=True,
        schedule={'interval': '5m'},
        params={},
        rule_type_id='log.alert',
        actions=[],
    )
    defaults.update(kwargs)
    return defaults


class TestElasticAdapterParseRules:
    def test_includes_enabled_rule(self):
        adapter = ElasticAdapter()
        result = adapter.parse_rules([_make_item(enabled=True)])
        assert len(result) == 1
        assert result[0].name == 'My Rule'

    def test_excludes_disabled_rule(self):
        adapter = ElasticAdapter()
        result = adapter.parse_rules([_make_item(enabled=False)])
        assert result == []

    def test_excludes_rule_missing_enabled_field(self):
        item = _make_item()
        del item['enabled']
        adapter = ElasticAdapter()
        assert adapter.parse_rules([item]) == []

    def test_filters_disabled_while_keeping_enabled(self):
        adapter = ElasticAdapter()
        items = [
            _make_item(id='rule-1', name='Enabled Rule', enabled=True),
            _make_item(id='rule-2', name='Disabled Rule', enabled=False),
        ]
        result = adapter.parse_rules(items)
        assert len(result) == 1
        assert result[0].name == 'Enabled Rule'
