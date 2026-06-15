## How to open

With the app running:

```bash
uvicorn app.main:app --reload
python scripts/load_test.py
```

Open **http://127.0.0.1:8000/dashboard** in your browser. Data refreshes every 20 seconds from `/metrics/dashboard`.1. Latency P50/P95/P99
2. Traffic (request count or QPS)
3. Error rate with breakdown
4. Cost over time
5. Tokens in/out
6. Quality proxy (heuristic, thumbs, or regenerate rate)

Quality bar:
- default time range = 1 hour
- auto refresh every 15-30 seconds
- visible threshold/SLO line
- units clearly labeled
- no more than 6-8 panels on the main layer
