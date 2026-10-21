# Comparative ETL evaluation

Run in the project root on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install pandas psutil matplotlib
python -m benchmarks.compare_etl --repeats 5 --sizes 1000 10000 100000
```

Outputs: `reports/comparative_results.csv`, `reports/comparative_summary.csv`, `reports/comparative_execution_time.png`.

## Scope and interpretation

The source files contain transaction rows without explicit transaction IDs and product/store dimension rows without IDs. The benchmark assigns 1-based product and store IDs from CSV row order, consistent with the generated dataset design.

The existing `scripts/transform.py` builds category, store and daily aggregate tables from PostgreSQL. This benchmark reproduces **the same aggregate logic**, but uses the CSV files as a common input, and runs in memory to isolate Python row-by-row versus Pandas vectorised transformation strategies. It does **not** benchmark PostgreSQL loading or full end-to-end ETL. Do not describe these results as end-to-end PostgreSQL performance or as evidence against all commercial ETL systems.

Correctness validation occurs before timed runs. The benchmark compares category/store/day counts, total amounts and averages, using integer cents for reproducibility. Runs alternate execution order. CPU-core-equivalent percent can exceed 100% on multi-core systems; sampled peak RSS is approximate.

Do not combine historical ETL measurements with these timings: they measure different workloads. Run on the same machine with similar background load and document hardware, software versions, repetition count, and limitations.
