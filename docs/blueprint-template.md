# Day 13 Observability Lab Report

> **Instruction**: Fill in all sections below. This report is designed to be parsed by an automated grading assistant. Ensure all tags (e.g., `[GROUP_NAME]`) are preserved.

## 1. Team Metadata
- [GROUP_NAME]: 2A202600979 - Ngo Thi Anh
- [REPO_URL]: https://github.com/AnhMin/2A202600979-NgoThiAnh-Day13
- [MEMBERS]:
  - Member A: Ngo Thi Anh | Role: Logging & PII
  - Member B: Ngo Thi Anh | Role: Tracing & Enrichment
  - Member C: Ngo Thi Anh | Role: SLO & Alerts
  - Member D: Ngo Thi Anh | Role: Load Test & Dashboard
  - Member E: Ngo Thi Anh | Role: Demo & Report

---

## 2. Group Performance (Auto-Verified)
- [VALIDATE_LOGS_FINAL_SCORE]: 100/100
- [TOTAL_TRACES_COUNT]: >= 20 (Langfuse — traces named `LabAgent.run`)
- [PII_LEAKS_FOUND]: 0

---

## 3. Technical Evidence (Group)

### 3.1 Logging & Tracing
- [EVIDENCE_CORRELATION_ID_SCREENSHOT]: docs/evidence/correlation-id-log.png
- [EVIDENCE_PII_REDACTION_SCREENSHOT]: docs/evidence/pii-redaction-log.png
- [EVIDENCE_TRACE_WATERFALL_SCREENSHOT]: docs/evidence/langfuse-trace-waterfall.png
- [TRACE_WATERFALL_EXPLANATION]: Trace `LabAgent.run` (agent span) gồm retrieve → LLM generate. Span có metadata `doc_count`, `query_preview` (đã scrub PII), `usage_details` (input/output tokens). Tags: `lab`, feature (`qa`/`summary`), model `claude-sonnet-4-5`. user_id được hash SHA256 12 ký tự; session_id giữ nguyên để group theo phiên.

### 3.2 Dashboard & SLOs
- [DASHBOARD_6_PANELS_SCREENSHOT]: docs/evidence/dashboard-6-panels.png
- [SLO_TABLE]:
| SLI | Target | Window | Current Value |
|---|---:|---|---:|
| Latency P95 | < 3000ms | 28d | ~2651ms (khi `rag_slow` bật) / ~155ms (bình thường) |
| Error Rate | < 2% | 28d | 0% (bình thường) / 100% (khi `tool_fail` bật) |
| Cost Budget | < $2.5/day | 1d | ~$0.002/req (bình thường) / ~$0.005/req (khi `cost_spike` bật) |

Dashboard URL: http://127.0.0.1:8000/dashboard (6 panels, auto-refresh 20s, có đường SLO).

### 3.3 Alerts & Runbook
- [ALERT_RULES_SCREENSHOT]: docs/evidence/alert-rules-firing.png
- [SAMPLE_RUNBOOK_LINK]: docs/alerts.md#1-high-latency-p95

3 alert rules trong `config/alert_rules.yaml`:
1. `high_latency_p95` (P2) — P95 > 2500ms → runbook #1
2. `high_error_rate` (P1) — error rate > 5% → runbook #2
3. `cost_budget_spike` (P2) — avg cost > 2× baseline → runbook #3

Kiểm tra live: `GET http://127.0.0.1:8000/alerts` hoặc `python scripts/test_alerts.py`

---

## 4. Incident Response (Group)
- [SCENARIO_NAME]: rag_slow
- [SYMPTOMS_OBSERVED]: Latency P95 tăng từ ~155ms lên ~2651ms; dashboard panel 1 vượt SLO 3000ms gần ngưỡng; alert `high_latency_p95` chuyển sang FIRING; log `response_sent` có `latency_ms` cao hơn bình thường.
- [ROOT_CAUSE_PROVED_BY]:
  - Metrics: `/metrics` → `latency_p95: 2651.0`
  - Alerts: `/alerts` → `high_latency_p95` status FIRING
  - Logs: event `incident_enabled` với `payload.name = "rag_slow"`
  - Code: `app/mock_rag.py` — `STATE["rag_slow"]` → `time.sleep(2.5)`
- [FIX_ACTION]: `python scripts/inject_incident.py --scenario rag_slow --disable` — latency trở về ~155ms, alert hết FIRING.
- [PREVENTIVE_MEASURE]: Thêm timeout + fallback retrieval; alert P95 liên kết runbook; theo dõi span RAG trên Langfuse để phát hiện sớm trước khi vượt SLO 3000ms.

---

## 5. Individual Contributions & Evidence

### Ngo Thi Anh (Member A — Logging & PII)
- [TASKS_COMPLETED]: Correlation ID middleware (`app/middleware.py`); PII scrubber `scrub_event` trong `app/logging_config.py`; regex patterns trong `app/pii.py`; `validate_logs.py` đạt 100/100.
- [EVIDENCE_LINK]: app/middleware.py, app/logging_config.py, app/pii.py

### Ngo Thi Anh (Member B — Tracing & Enrichment)
- [TASKS_COMPLETED]: Log enrichment `bind_contextvars` trong `app/main.py`; Langfuse 4.x tracing (`app/tracing.py`); `@observe` + `propagate_trace_attributes` trong `app/agent.py`; `load_dotenv()` để nạp Langfuse keys.
- [EVIDENCE_LINK]: app/main.py, app/tracing.py, app/agent.py

### Ngo Thi Anh (Member C — SLO & Alerts)
- [TASKS_COMPLETED]: SLO trong `config/slo.yaml`; 3 alert rules + engine `app/alerts.py`; endpoint `/alerts`; script `scripts/test_alerts.py`; runbook `docs/alerts.md`.
- [EVIDENCE_LINK]: config/alert_rules.yaml, app/alerts.py, scripts/test_alerts.py, docs/alerts.md

### Ngo Thi Anh (Member D — Load Test & Dashboard)
- [TASKS_COMPLETED]: Dashboard 6 panels (`static/dashboard.html`); time-series metrics (`app/metrics.py`); endpoints `/dashboard`, `/metrics/dashboard`; load test + incident injection scripts.
- [EVIDENCE_LINK]: static/dashboard.html, app/metrics.py, scripts/load_test.py

### Ngo Thi Anh (Member E — Demo & Report)
- [TASKS_COMPLETED]: Hoàn thiện lab flow 8 bước; blueprint report; demo flow: health → load_test → dashboard → alerts → Langfuse traces → incident debug.
- [EVIDENCE_LINK]: docs/blueprint-template.md

---

## 6. Bonus Items (Optional)
- [BONUS_COST_OPTIMIZATION]: Chưa triển khai (có thể route request dễ sang model rẻ hơn khi `cost_spike` bật).
- [BONUS_AUDIT_LOGS]: Chưa triển khai (`AUDIT_LOG_PATH` đã có trong `.env.example`).
- [BONUS_CUSTOM_METRIC]: Dashboard quality score heuristic + alert engine tùy chỉnh (`app/alerts.py`).
