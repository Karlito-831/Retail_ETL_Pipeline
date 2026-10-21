# Two-site Retail ETL — Setup and checks

## Before starting

1. Open the **inner** `Retail _ETL_Project` directory in VS Code.
2. Create a virtual environment (optional): `python -m venv .venv`.
3. Install requirements: `python -m pip install -r requirements.txt`.
4. Copy `.env.example` to `.env` and fill in your **existing** PostgreSQL credentials. Do not publish `.env`.
5. Ensure PostgreSQL is running and the existing retail tables are populated. Do not reload the source data.

## Start both websites (two separate PowerShell terminals)

Terminal A: `python traditional_app.py` — http://127.0.0.1:5001

Terminal B: `python app.py` — http://127.0.0.1:5000

Or run `START_WEBSITES.bat` on Windows.

## Pages to check

- Proposed: `/`, `/analytics`, `/products`, `/customers`, `/stores`, `/reports`, `/evaluation`.
- Traditional: `/`, `/pipeline`, `/transactions`, `/analytics`, `/evaluation`.
- Styling: `/static/css/style.css` on port 5000; `/static/css/baseline.css` on port 5001.
- If styles look outdated, use Ctrl+Shift+R.

## Evaluation validity

The existing benchmark measures CSV extraction and analytical transformation, **not PostgreSQL writes** or web page latency. Re-run with `python -m benchmarks.compare_etl --repeats 5 --sizes 1000 10000 100000` to obtain new measurements on your machine. Results are not a comparison against all commercial ETL platforms.

## Validation scope

Static analysis and Flask route tests can run without the user's PostgreSQL server. Live connection to your PostgreSQL instance must be verified locally.
