import re
from typing import List, Optional

from alert_monitoring.api.domain.models.alert import Alert
from alert_monitoring.api.domain.models.default_alert import DefaultAlert
from alert_monitoring.api.driven.prometheus_repository.models.prometheus_model import PrometheusRule
from alert_monitoring.api.driven.shared.alert_normalization import (
    BOOL_CHANNEL_LABELS,
    DEFAULT_ALERT_DISPLAY,
    build_exclusion_updates,
    display_canal,
    environments_or_all,
    extract_adhoc_chips,
)


def is_default_rule(rule: PrometheusRule) -> bool:
    return (
        str(rule.labels.get("alertype", "")).lower() == "default"
        and rule.group_name.lower().startswith("default")
    )


class PrometheusMapper:
    def to_domain(self, rules: List[PrometheusRule]) -> List[Alert]:
        return [self._map_rule(rule) for rule in rules]

    def to_adhoc_alerts(self, rules: List[PrometheusRule]) -> List[Alert]:
        return [alert for alert in self.to_domain(rules) if alert.alert_type != "Por Defecto"]

    def to_default_alerts(self, rules: List[PrometheusRule]) -> List[DefaultAlert]:
        default_rules = [rule for rule in rules if is_default_rule(rule)]
        if not default_rules:
            return []

        exclusions = build_exclusion_updates(default_rules)

        raw_descriptions: dict[str, str] = {}
        first_severity: dict[str, str] = {}
        first_channel: dict[str, str] = {}
        for rule in default_rules:
            raw_name = rule.alert.split()[0] if rule.alert else None
            if not raw_name:
                continue
            if raw_name not in raw_descriptions:
                raw_descriptions[raw_name] = rule.annotations.get("message", "")
            if raw_name not in first_severity:
                first_severity[raw_name] = rule.labels.get("severity", "")
            if raw_name not in first_channel:
                first_channel[raw_name] = self._infer_channel(rule.labels) or ""

        default_alerts: List[DefaultAlert] = []
        for raw_name, (excl_ns, incl_ns, excl_jobs) in exclusions.items():
            translation = DEFAULT_ALERT_DISPLAY.get(raw_name)
            default_alerts.append(DefaultAlert(
                raw_name=raw_name,
                display_name=translation[0] if translation else raw_name,
                raw_description=raw_descriptions.get(raw_name) or None,
                display_description=translation[1] if translation else None,
                severity=first_severity.get(raw_name) or None,
                notification_channel=first_channel.get(raw_name) or None,
                excluded_namespaces=excl_ns,
                included_namespaces=incl_ns,
                excluded_jobs=excl_jobs,
            ))
        return default_alerts

    def _map_rule(self, rule: PrometheusRule) -> Alert:
        labels = rule.labels
        is_default = is_default_rule(rule)
        raw_name = rule.alert.split()[0] if rule.alert else rule.alert
        name = raw_name if is_default else rule.alert
        description = rule.annotations.get("message", "Sin descripción")

        alert_type = "Por Defecto" if is_default else "Ad-hoc"
        return Alert(
            name=name,
            description=description,
            source_tool="Prometheus",
            severity=labels.get("severity", "unknown"),
            chips=extract_adhoc_chips(rule.expr) if not is_default else [],
            environments=["pro"] if is_default else environments_or_all(self._infer_environments(rule)),
            solution=self._infer_solution(rule),
            notification_channel=self._infer_channel(labels),
            alert_type=alert_type,
            cluster=rule.cluster_name or None,
            prometheus_name=raw_name if is_default else None,
        )

    def _infer_solution(self, rule: PrometheusRule) -> str:
        solucion = rule.labels.get("solucion")
        if solucion:
            return solucion
        group_name = rule.group_name or ""
        cleaned = re.sub(r"\.rules$", "", group_name)
        cleaned = re.sub(r"-cr[ií]ticas$", "", cleaned)
        return cleaned or "unknown"

    def _infer_channel(self, labels: dict) -> Optional[str]:
        canal = labels.get("canal")
        if canal:
            return display_canal(canal)
        for label, display in BOOL_CHANNEL_LABELS:
            if labels.get(label) == "true":
                return display
        return None

    def _infer_environments(self, rule: PrometheusRule) -> List[str]:
        labels = rule.labels

        label_envs = [
            val for val in (labels.get(key, "").lower() for key in ("environment", "env"))
            if val and "{{" not in val
        ]
        if label_envs:
            return label_envs

        expr_envs: set[str] = set()
        for match in re.findall(r'environment(?:=~|=)["\']([^"\']+)["\']', rule.expr):
            for part in match.split("|"):
                clean = self._clean(part)
                if clean:
                    expr_envs.add(clean)
        return list(expr_envs)

    def _clean(self, value: str) -> str:
        return value.replace(".*", "").replace(".+", "").replace("^", "").replace("$", "").strip()
