from app.alerts import evaluate_alerts, load_rules


def test_load_rules_has_three_alerts() -> None:
    rules = load_rules()
    names = {rule["name"] for rule in rules}
    assert names == {"high_latency_p95", "high_error_rate", "cost_budget_spike"}


def test_high_error_rate_alert_fires(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.alerts.snapshot",
        lambda: {
            "traffic": 10,
            "latency_p95": 150.0,
            "error_rate_pct": 10.0,
            "avg_cost_usd": 0.002,
            "total_cost_usd": 0.02,
        },
    )
    monkeypatch.setattr("app.alerts._hourly_cost_usd", lambda: 0.01)
    payload = evaluate_alerts()
    firing = {item["name"] for item in payload["firing"]}
    assert "high_error_rate" in firing
