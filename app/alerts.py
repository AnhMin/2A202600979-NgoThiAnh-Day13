from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml

from .metrics import METRIC_POINTS, SLO, snapshot

RULES_PATH = Path(__file__).resolve().parent.parent / "config" / "alert_rules.yaml"
COST_BASELINE_USD = 0.002


def load_rules() -> list[dict[str, Any]]:
    data = yaml.safe_load(RULES_PATH.read_text(encoding="utf-8"))
    return list(data.get("alerts", []))


def _hourly_cost_usd() -> float:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
    return round(
        sum(float(p["cost_usd"]) for p in METRIC_POINTS if datetime.fromisoformat(p["ts"]) >= cutoff),
        4,
    )


def _evaluate_rule(rule: dict[str, Any], snap: dict[str, Any]) -> dict[str, Any]:
    name = rule["name"]
    metric = rule.get("metric", "")
    threshold = rule.get("threshold")
    operator = rule.get("operator", ">")
    result: dict[str, Any] = {
        "name": name,
        "severity": rule.get("severity"),
        "runbook": rule.get("runbook"),
        "condition": rule.get("condition"),
        "status": "OK",
        "metric": metric,
        "threshold": threshold,
        "current_value": None,
    }

    if name == "high_latency_p95":
        current = float(snap["latency_p95"])
        result["current_value"] = current
        if current > float(threshold):
            result["status"] = "FIRING"

    elif name == "high_error_rate":
        current = float(snap["error_rate_pct"])
        result["current_value"] = current
        if current > float(threshold):
            result["status"] = "FIRING"

    elif name == "cost_budget_spike":
        current = float(snap["avg_cost_usd"])
        baseline = float(rule.get("baseline_usd", COST_BASELINE_USD))
        multiplier = float(rule.get("multiplier", 2))
        result["current_value"] = current
        result["threshold"] = round(baseline * multiplier, 4)
        result["metric"] = "avg_cost_usd"
        if current > baseline * multiplier and snap["traffic"] >= int(rule.get("min_traffic", 3)):
            result["status"] = "FIRING"

    else:
        result["status"] = "UNKNOWN"

    result["operator"] = operator
    return result


def evaluate_alerts() -> dict[str, Any]:
    snap = snapshot()
    rules = load_rules()
    evaluated = [_evaluate_rule(rule, snap) for rule in rules]
    firing = [item for item in evaluated if item["status"] == "FIRING"]
    return {
        "slo": SLO,
        "snapshot": snap,
        "hourly_cost_usd": _hourly_cost_usd(),
        "rules": evaluated,
        "firing_count": len(firing),
        "firing": firing,
        "all_ok": len(firing) == 0,
    }
