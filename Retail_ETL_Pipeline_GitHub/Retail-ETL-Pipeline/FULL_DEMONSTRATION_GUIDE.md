# Two-system ETL evaluation demonstration

## Start

From this project folder, with the outer-folder `.venv` already activated:

```powershell
python -m pip install -r requirements.txt
python -m pip install plotly
python traditional_app.py
```

Open http://127.0.0.1:5001. In a **second terminal** run:

```powershell
python app.py
```

Open http://127.0.0.1:5000. The proposed artifact requires the existing PostgreSQL database and a valid `.env` configuration. The original uploaded ZIP's `.env` was intentionally **not** included, because it can contain a database password. Copy your existing `.env` into the project root locally, never share it publicly.

Alternatively double-click `START_WEBSITES.bat` after dependencies are installed.

## Demo sequence

1. Baseline dashboard: show the actual 100K transaction CSV, sequential pipeline, and analytical summaries.
2. Proposed artifact: show existing PostgreSQL-backed dashboard and analytics.
3. Open Performance Evaluation on both sites: 1K, 10K, 100K comparison, five runs each, output-equivalence validation.
4. Explain that the traditional baseline wins at 1K and 10K, whereas Pandas wins at 100K; the result is workload-dependent.

## Measurements and academic integrity

- `reports/observed_terminal_timings.csv` contains the **rounded 4-decimal timings copied from your October 18 terminal output**, not fabricated runs. `reports/observed_terminal_summary.csv` derives from those rounded values.
- If you copy your actual `reports/comparative_results.csv` from your previous successful run into this project's `reports` folder, both sites automatically prefer those full-precision values.
- The benchmark compares **CSV extraction and analytical transformation**. It does NOT measure PostgreSQL inserts, full end-to-end ETL, or website response times. The baseline is a conventional sequential Python implementation, not a commercial ETL suite.
- No database is modified by the traditional website. It computes cached summaries from the same source CSV as the benchmark.
- Re-run `python -m benchmarks.compare_etl --repeats 5 --sizes 1000 10000 100000` to collect fresh measurements. The script overwrites the full-precision report; archive your earlier results first.
- The original proposed app requires PostgreSQL to be running and the original `.env` credentials. The baseline site works without PostgreSQL.

## File map

- `traditional_app.py`: baseline Flask app, port 5001
- `app.py`: existing proposed artifact, port 5000, plus `/evaluation`
- `evaluation_data.py`: common results reader
- `templates/baseline/`: shared baseline/evaluation layouts
- `static/css/baseline.css`: responsive dark theme
- `benchmarks/compare_etl.py`: tested experimental implementations
- `reports/observed_terminal_timings.csv`: measured user-reported rounded timings

## Research caveat

A stronger claim about *complete ETL* superiority would require a separate, controlled PostgreSQL loading benchmark with equivalent database schema, constraints, transaction behavior, isolation, and correctness checks. Do not describe the present timing results as end-to-end database ETL.
