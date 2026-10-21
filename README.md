# Retail_ETL_Pipeline
## Retail ETL Pipeline — Implementation and Performance Evaluation

This project implements and evaluates an Extract, Transform, Load (ETL) pipeline designed to process synthetic retail transactional data.

Built using Python, Pandas, PostgreSQL, and Flask, the system extracts retail data, performs data cleaning and analytical transformations, loads processed results into PostgreSQL, and provides a web-based dashboard for viewing retail analytics.

The pipeline was experimentally evaluated using datasets containing 1,000, 10,000, and 100,000 transactions. Each workload was tested five times to assess execution time, throughput, CPU consumption, memory usage, and scalability.

The project also compares traditional Python processing with Pandas-based transformations to investigate performance differences across increasing data volumes.

**Key technologies:** Python, Pandas, PostgreSQL, SQLAlchemy, Flask, Faker, and psutil.
