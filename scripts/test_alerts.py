from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import httpx

BASE_URL = "http://127.0.0.1:8000"
ROOT = Path(__file__).resolve().parent.parent


def post(path: str) -> dict:
    r = httpx.post(f"{BASE_URL}{path}", timeout=30.0)
    r.raise_for_status()
    return r.json()


def get_alerts() -> dict:
    r = httpx.get(f"{BASE_URL}/alerts", timeout=10.0)
    r.raise_for_status()
    return r.json()


def run_load_test() -> None:
    subprocess.run([sys.executable, "scripts/load_test.py"], check=True, cwd=ROOT)


def disable_all() -> None:
    for scenario in ("rag_slow", "tool_fail", "cost_spike"):
        post(f"/incidents/{scenario}/disable")


def print_result(title: str, payload: dict) -> None:
    print(f"\n=== {title} ===")
    for rule in payload["rules"]:
        status = rule["status"]
        marker = "FIRING" if status == "FIRING" else "ok"
        print(f"[{marker}] {rule['name']}: {rule.get('current_value')} (threshold={rule.get('threshold')})")
    print(f"firing_count={payload['firing_count']} all_ok={payload['all_ok']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Test alert rules against live incidents")
    parser.add_argument("--skip-load", action="store_true", help="Skip load_test.py calls")
    args = parser.parse_args()

    try:
        httpx.get(f"{BASE_URL}/health", timeout=5.0).raise_for_status()
    except Exception as exc:
        print(f"Error: app not reachable at {BASE_URL}. Start uvicorn first. ({exc})")
        sys.exit(1)

    disable_all()
    print_result("Baseline (no incidents)", get_alerts())

    scenarios = [
        ("rag_slow", "high_latency_p95"),
        ("tool_fail", "high_error_rate"),
        ("cost_spike", "cost_budget_spike"),
    ]

    for scenario, expected in scenarios:
        disable_all()
        post(f"/incidents/{scenario}/enable")
        if not args.skip_load:
            run_load_test()
        payload = get_alerts()
        print_result(f"Scenario: {scenario}", payload)
        fired = {item["name"] for item in payload["firing"]}
        if expected in fired:
            print(f"+ PASSED expected alert fired: {expected}")
        else:
            print(f"- FAILED expected alert NOT fired: {expected}")
        post(f"/incidents/{scenario}/disable")

    disable_all()
    print("\n--- Alert Test Complete ---")


if __name__ == "__main__":
    main()
