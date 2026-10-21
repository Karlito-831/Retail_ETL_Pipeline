import pandas as pd
from pathlib import Path
from database import get_engine

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA = BASE_DIR / "data" / "raw"

engine = get_engine()


def load_csv(filename, table_name):
    file_path = RAW_DATA / filename

    print(f"Loading {filename}...")

    df = pd.read_csv(file_path)

    df.to_sql(
        table_name,
        engine,
        if_exists="append",
        index=False
    )

    print(f"✓ {len(df):,} rows inserted into {table_name}")


def main():

    load_csv("customers.csv", "customers")
    load_csv("products.csv", "products")
    load_csv("stores.csv", "stores")
    load_csv("transactions.csv", "transactions")

    print("\n====================================")
    print("All data successfully loaded!")
    print("====================================")


if __name__ == "__main__":
    main()