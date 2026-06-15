# Evidence Screenshots — Day 13 Lab

Chụp 5 ảnh dưới đây và lưu đúng tên file. Blueprint tham chiếu các path này.

## 1. `correlation-id-log.png`

**Chụp gì:** Một vài dòng JSON trong `data/logs.jsonl` (hoặc terminal) thấy cùng `correlation_id` xuyên suốt `request_received` và `response_sent`.

**Cách lấy:**
```powershell
python scripts/load_test.py
Get-Content data/logs.jsonl -Tail 4
```

**Cần thấy:** `"correlation_id": "req-xxxxxxxx"` (không phải `MISSING`).

---

## 2. `pii-redaction-log.png`

**Chụp gì:** Log line có email/SĐT/thẻ đã được thay bằng `[REDACTED_EMAIL]`, `[REDACTED_PHONE_VN]`, v.v.

**Gợi ý:** Dòng có `message_preview` từ query s09 (credit card) hoặc s01 (email).

```powershell
Select-String -Path data/logs.jsonl -Pattern "REDACTED"
```

---

## 3. `langfuse-trace-waterfall.png`

**Chụp gì:** Langfuse UI — một trace `LabAgent.run` mở full waterfall.

**Cách:**
1. Gửi request: `python scripts/load_test.py`
2. Mở https://cloud.langfuse.com → **Traces**
3. Chọn trace mới nhất tên `LabAgent.run`
4. Chụp màn hình có: user_id (hash), session_id, tags, metadata

**Cần:** ≥ 10 traces trong list (chụp thêm list nếu giảng viên yêu cầu).

---

## 4. `dashboard-6-panels.png`

**Chụp gì:** Toàn bộ dashboard 6 panel.

**Cách:**
1. App đang chạy: `uvicorn app.main:app --reload`
2. Gửi traffic: `python scripts/load_test.py`
3. Mở http://127.0.0.1:8000/dashboard
4. Chụp khi có data trên chart (không để trống)

**Cần thấy:** 6 panel + stat cards phía trên + đường SLO (vàng).

---

## 5. `alert-rules-firing.png`

**Chụp gì:** Alert đang FIRING sau khi bật incident.

**Cách (latency alert):**
```powershell
python scripts/inject_incident.py --scenario rag_slow
python scripts/load_test.py
```
Mở http://127.0.0.1:8000/alerts — chụp JSON hoặc terminal:
```powershell
python scripts/test_alerts.py
```
Thấy `[FIRING] high_latency_p95`.

Tắt incident sau khi chụp:
```powershell
python scripts/inject_incident.py --scenario rag_slow --disable
```

---

## Checklist trước khi nộp

- [ ] 5 file PNG đặt trong `docs/evidence/`
- [ ] `python scripts/validate_logs.py` → 100/100
- [ ] Langfuse có ≥ 10 traces
- [ ] `docs/blueprint-template.md` đã điền đủ
- [ ] Code đã commit lên GitHub
