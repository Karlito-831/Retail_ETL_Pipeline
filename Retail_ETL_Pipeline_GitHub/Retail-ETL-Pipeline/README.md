# Retail ETL Pipeline — Implementation and Performance Evaluation

Research project implementing a retail transactional-data ETL prototype with Python, Pandas, PostgreSQL, SQLAlchemy and Flask. Synthetic data is used to compare workloads of 1,000, 10,000 and 100,000 transactions.

## Setup

1. Install Python and PostgreSQL, and create a PostgreSQL database for this project.
2. Install dependencies: `python -m pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and enter **your own local PostgreSQL credentials**. Never commit `.env`.
4. Consult `SETUP_AND_TESTING.md` and `FULL_DEMONSTRATION_GUIDE.md` for the project-specific setup and execution steps.
5. Run `python traditional_app.py` for the traditional demonstration (port 5001), or `python app.py` for the PostgreSQL-backed proposed artefact (port 5000).

## Evaluation

- Comparative analytical benchmark: `python -m benchmarks.compare_etl --repeats 5 --sizes 1000 10000 100000`
- Full PostgreSQL ETL evaluation: `python full_etl_experiment.py --repeats 5 --sizes 1000 10000 100000`

These are **different experiments**. The comparative benchmark measures analytical processing without PostgreSQL loading. The full evaluation includes database loading and writes to a separate experiment schema. See the `reports/` folder for recorded outputs.

## Security

The included `.env.example` contains **placeholder values only**. Supply credentials locally in `.env`. Never publish real passwords, connection strings containing passwords, or database backups.
