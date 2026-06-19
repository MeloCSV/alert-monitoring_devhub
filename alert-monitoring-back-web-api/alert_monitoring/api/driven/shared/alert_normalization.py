import logging
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import yaml

ALL_ENVIRONMENTS: Tuple[str, ...] = ("dev", "itg", "pre", "pro")

_logger = logging.getLogger(__name__)

_DISPLAY_FILE = Path(__file__).parent / "default_alerts_display.yml"


def _load_default_alert_display() -> Dict[str, Tuple[str, str]]:
    if not _DISPLAY_FILE.exists():
        _logger.warning("No se encontró %s; no habrá traducciones de alertas por defecto.", _DISPLAY_FILE)
        return {}
    with open(_DISPLAY_FILE, encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return {
        raw_name: (entry["display_name"], entry["display_description"])
        for raw_name, entry in data.items()
        if isinstance(entry, dict) and "display_name" in entry and "display_description" in entry
    }

NAMESPACE_LABEL_KEYS: Tuple[str, ...] = ("namespace", "exported_namespace", "backend_target_name", "backend_name")
JOB_LABEL_KEYS: Tuple[str, ...] = ("job_name", "deployment", "horizontalpodautoscaler")

# Etiquetas de job que se muestran como chip en alertas Ad-hoc cuando hay granularidad de job.
ADHOC_JOB_CHIP_LABEL_KEYS: Tuple[str, ...] = (
    "job_name", "deployment", "horizontalpodautoscaler", "cronjob",
)

# Lookup de traducción cargado desde default_alerts_display.yml (mismo directorio).
# NO es la fuente de verdad de qué alertas existen; eso lo son las Prometheus rules.
# Si un raw_name nuevo aparece en Prometheus y no está en el YAML, se mostrará el
# raw_name en la UI hasta que alguien añada la entrada correspondiente.
DEFAULT_ALERT_DISPLAY: Dict[str, Tuple[str, str]] = _load_default_alert_display()

CANAL_DISPLAY_NAMES: Dict[str, str] = {
    "msteams": "Teams",
    "teams": "Teams",
    "omi": "ServiceNow",
    "jira": "Jira",
    "mail": "Mail",
    "alertmanager": "AlertManager",
}

BOOL_CHANNEL_LABELS: Tuple[Tuple[str, str], ...] = (
    ("msteams", "Teams"),
    ("omi", "ServiceNow"),
    ("jira", "Jira"),
    ("mail", "Mail"),
)

_ENV_PATTERN = re.compile(r"\b(dev|itg|pre|pro)\d*\b", re.IGNORECASE)


def display_canal(canal: Optional[str]) -> Optional[str]:
    if not canal:
        return None
    return CANAL_DISPLAY_NAMES.get(canal.lower(), canal)


def resolve_channels_from_labels(labels: Dict[str, str]) -> List[str]:
    matches: List[str] = []
    for key, display in BOOL_CHANNEL_LABELS:
        if str(labels.get(key, "")).lower() == "true" and display not in matches:
            matches.append(display)
    return matches


def detect_environments(texts: Iterable[Optional[str]]) -> List[str]:
    found: List[str] = []
    for text in texts:
        if not text:
            continue
        for match in _ENV_PATTERN.findall(text):
            env = match.lower()
            if env not in found:
                found.append(env)
    return found


def environments_or_all(envs: List[str]) -> List[str]:
    return envs if envs else list(ALL_ENVIRONMENTS)


def extract_label_alternatives(expr: Optional[str], keys: Iterable[str], exclude: bool) -> List[str]:
    """Extract the alternatives from a PromQL selector for the given label keys.

    Args:
        expr: PromQL expression string.
        keys: Label names to look for (e.g. ``namespace``, ``job_name``).
        exclude: If True look for ``!~`` selectors; if False look for ``=~``.
    """
    if not expr:
        return []
    operator = "!~" if exclude else "=~"
    alternatives: List[str] = []
    for key in keys:
        regex = rf'{key}\s*{re.escape(operator)}\s*"([^"]+)"'
        for match in re.findall(regex, expr):
            for part in _split_top_level_alternatives(match):
                if part and part not in alternatives:
                    alternatives.append(part)
    return alternatives


def build_exclusion_updates(default_rules) -> dict:
    """Merge exclusion patterns from all default Prometheus rule instances grouped by raw_name."""
    buckets: dict[str, dict] = defaultdict(lambda: {"excl_ns": set(), "incl_ns": set(), "excl_jobs": set()})
    for rule in default_rules:
        raw_name = rule.alert.split()[0] if rule.alert else None
        if not raw_name:
            continue
        bucket = buckets[raw_name]
        bucket["excl_ns"].update(extract_label_alternatives(rule.expr, NAMESPACE_LABEL_KEYS, exclude=True))
        bucket["incl_ns"].update(extract_label_alternatives(rule.expr, NAMESPACE_LABEL_KEYS, exclude=False))
        bucket["excl_jobs"].update(extract_label_alternatives(rule.expr, JOB_LABEL_KEYS, exclude=True))
    return {
        raw_name: (sorted(b["excl_ns"]), sorted(b["incl_ns"]), sorted(b["excl_jobs"]))
        for raw_name, b in buckets.items()
    }


def clean_label_value(value: str) -> str:
    """Limpia el valor de una etiqueta para mostrarlo: quita anclas/comodines de regex."""
    cleaned = value.strip()
    if cleaned.startswith("^"):
        cleaned = cleaned[1:]
    if cleaned.endswith("$"):
        cleaned = cleaned[:-1]
    for suffix in (".*", ".+"):
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)]
            break
    return cleaned.rstrip("-").strip()


def extract_adhoc_chips(expr: Optional[str]) -> List[str]:
    """Extrae chips para alertas Ad-hoc.

    Si hay selectores de job (job_name, deployment, etc.) se devuelven esos.
    Si solo hay selectores de namespace (namespace entero incluido), se devuelve
    lista vacía porque no hay granularidad adicional que mostrar.
    """
    if not expr:
        return []
    job_chips: List[str] = []
    for key in ADHOC_JOB_CHIP_LABEL_KEYS:
        regex = rf'{key}\s*=~?\s*"([^"]+)"'
        for match in re.findall(regex, expr):
            for raw in match.split("|"):
                cleaned = clean_label_value(raw)
                if cleaned and cleaned not in job_chips:
                    job_chips.append(cleaned)
    return job_chips


def _split_top_level_alternatives(pattern: str) -> List[str]:
    """Split a regex alternation string on top-level '|' only (not inside parentheses)."""
    parts: List[str] = []
    depth = 0
    current: List[str] = []
    for ch in pattern:
        if ch == "(":
            depth += 1
            current.append(ch)
        elif ch == ")":
            depth -= 1
            current.append(ch)
        elif ch == "|" and depth == 0:
            part = "".join(current).strip()
            if part:
                parts.append(part)
            current = []
        else:
            current.append(ch)
    if current:
        part = "".join(current).strip()
        if part:
            parts.append(part)
    return parts
