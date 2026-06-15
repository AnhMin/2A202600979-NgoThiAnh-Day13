from app.metrics import dashboard_payload, percentile, record_request


def test_percentile_basic() -> None:
    assert percentile([100, 200, 300, 400], 50) >= 100


def test_dashboard_payload_has_six_series() -> None:
    record_request(latency_ms=150, cost_usd=0.002, tokens_in=30, tokens_out=100, quality_score=0.8)
    payload = dashboard_payload()
    series = payload["series"]
    assert "latency_p50" in series
    assert "traffic" in series
    assert "error_rate_pct" in series
    assert "cost_usd_cumulative" in series
    assert "tokens_in" in series
    assert "quality_avg" in series
    assert payload["slo"]["latency_p95_ms"] == 3000