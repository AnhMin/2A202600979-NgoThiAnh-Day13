from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from statistics import mean

REQUEST_LATENCIES: list[int] = []
REQUEST_COSTS: list[float] = []
REQUEST_TOKENS_IN: list[int] = []
REQUEST_TOKENS_OUT: list[int] = []
ERRORS: Counter[str] = Counter()
TRAFFIC: int = 0
QUALITY_SCORES: list[float] = []

METRIC_POINTS: list[dict] = []
ERROR_EVENTS: list[dict] = []

SLO = {
    "latency_p95_ms": 3000,
    "error_rate_pct": 2.0,
    "quality_score_avg": 0.75,
    "daily_cost_usd": 2.5,
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _trim_series() -> None:
    cutoff = _now() - timedelta(hours=1)
    global METRIC_POINTS, ERROR_EVENTS
    METRIC_POINTS = [p for p in METRIC_POINTS if datetime.fromisoformat(p["ts"]) >= cutoff]
    ERROR_EVENTS = [e for e in ERROR_EVENTS if datetime.fromisoformat(e["ts"]) >= cutoff]


def record_request(latency_ms: int, cost_usd: float, tokens_in: int, tokens_out: int, quality_score: float) -> None:
    global TRAFFIC
    TRAFFIC += 1
    REQUEST_LATENCIES.append(latency_ms)
    REQUEST_COSTS.append(cost_usd)
    REQUEST_TOKENS_IN.append(tokens_in)
    REQUEST_TOKENS_OUT.append(tokens_out)
    QUALITY_SCORES.append(quality_score)
    METRIC_POINTS.append(
        {
            "ts": _now().isoformat(),
            "latency_ms": latency_ms,
            "cost_usd": cost_usd,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "quality_score": quality_score,
        }
    )
    _trim_series()


def record_error(error_type: str) -> None:
    ERRORS[error_type] += 1
    ERROR_EVENTS.append({"ts": _now().isoformat(), "error_type": error_type})
    _trim_series()


def percentile(values: list[int], p: int) -> float:
    if not values:
        return 0.0
    items = sorted(values)
    idx = max(0, min(len(items) - 1, round((p / 100) * len(items) + 0.5) - 1))
    return float(items[idx])


def snapshot() -> dict:
    error_total = sum(ERRORS.values())
    error_rate_pct = round((error_total / TRAFFIC * 100) if TRAFFIC else 0.0, 2)
    return {
        "traffic": TRAFFIC,
        "latency_p50": percentile(REQUEST_LATENCIES, 50),
        "latency_p95": percentile(REQUEST_LATENCIES, 95),
        "latency_p99": percentile(REQUEST_LATENCIES, 99),
        "avg_cost_usd": round(mean(REQUEST_COSTS), 4) if REQUEST_COSTS else 0.0,
        "total_cost_usd": round(sum(REQUEST_COSTS), 4),
        "tokens_in_total": sum(REQUEST_TOKENS_IN),
        "tokens_out_total": sum(REQUEST_TOKENS_OUT),
        "error_breakdown": dict(ERRORS),
        "error_rate_pct": error_rate_pct,
        "quality_avg": round(mean(QUALITY_SCORES), 4) if QUALITY_SCORES else 0.0,
    }


def _minute_key(ts: str) -> str:
    dt = datetime.fromisoformat(ts)
    return dt.strftime("%H:%M")


def dashboard_series() -> dict:
    _trim_series()
    request_buckets: dict[str, list[dict]] = defaultdict(list)
    error_buckets: dict[str, int] = defaultdict(int)

    for point in METRIC_POINTS:
        request_buckets[_minute_key(point["ts"])].append(point)
    for event in ERROR_EVENTS:
        error_buckets[_minute_key(event["ts"])] += 1

    labels = sorted(set(request_buckets.keys()) | set(error_buckets.keys()))
    if not labels and METRIC_POINTS:
        labels = [_minute_key(p["ts"]) for p in METRIC_POINTS[-10:]]

    latency_p50: list[float] = []
    latency_p95: list[float] = []
    latency_p99: list[float] = []
    traffic: list[int] = []
    error_rate: list[float] = []
    cost: list[float] = []
    tokens_in: list[int] = []
    tokens_out: list[int] = []
    quality: list[float] = []
    cumulative_cost = 0.0

    for label in labels:
        bucket = request_buckets.get(label, [])
        latencies = [int(p["latency_ms"]) for p in bucket]
        latency_p50.append(percentile(latencies, 50) if latencies else 0.0)
        latency_p95.append(percentile(latencies, 95) if latencies else 0.0)
        latency_p99.append(percentile(latencies, 99) if latencies else 0.0)
        traffic.append(len(bucket))
        bucket_cost = sum(float(p["cost_usd"]) for p in bucket)
        cumulative_cost += bucket_cost
        cost.append(round(cumulative_cost, 4))
        tokens_in.append(sum(int(p["tokens_in"]) for p in bucket))
        tokens_out.append(sum(int(p["tokens_out"]) for p in bucket))
        quality.append(round(mean([float(p["quality_score"]) for p in bucket]), 4) if bucket else 0.0)
        bucket_errors = error_buckets.get(label, 0)
        error_rate.append(round((bucket_errors / len(bucket) * 100) if bucket else 0.0, 2))

    return {
        "labels": labels,
        "latency_p50": latency_p50,
        "latency_p95": latency_p95,
        "latency_p99": latency_p99,
        "traffic": traffic,
        "error_rate_pct": error_rate,
        "cost_usd_cumulative": cost,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "quality_avg": quality,
        "error_breakdown": dict(ERRORS),
    }


def dashboard_payload() -> dict:
    return {
        "snapshot": snapshot(),
        "slo": SLO,
        "series": dashboard_series(),
        "window": "1h",
        "refresh_seconds": 20,
    }
