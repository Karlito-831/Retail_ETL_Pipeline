import pandas as pd
from database import get_engine

engine = get_engine()


# ============================================================
# SALES SUMMARY
# ============================================================

def create_sales_summary():

    print("Creating Sales Summary...")

    transactions = pd.read_sql(
        "SELECT * FROM transactions",
        engine
    )

    products = pd.read_sql(
        "SELECT * FROM products",
        engine
    )

    sales = transactions.merge(
        products,
        on="product_id",
        how="left"
    )

    sales_summary = (
        sales.groupby("category")
        .agg(
            Total_Revenue=("total_amount", "sum"),
            Total_Orders=("transaction_id", "count"),
            Average_Order_Value=("total_amount", "mean")
        )
        .reset_index()
    )

    sales_summary.to_sql(
        "sales_summary",
        engine,
        if_exists="replace",
        index=False
    )

    print("✓ sales_summary created.")


# ============================================================
# STORE SUMMARY
# ============================================================

def create_store_summary():

    print("Creating Store Summary...")

    transactions = pd.read_sql(
        "SELECT * FROM transactions",
        engine
    )

    stores = pd.read_sql(
        "SELECT * FROM stores",
        engine
    )

    sales = transactions.merge(
        stores,
        on="store_id",
        how="left"
    )

    summary = (
        sales.groupby(
            ["store_id", "store_name", "city"]
        )
        .agg(
            Revenue=("total_amount", "sum"),
            Orders=("transaction_id", "count"),
            Average_Order_Value=("total_amount", "mean")
        )
        .reset_index()
    )

    summary.to_sql(
        "store_summary",
        engine,
        if_exists="replace",
        index=False
    )

    print("✓ store_summary created.")


# ============================================================
# DAILY SALES
# ============================================================

def create_daily_sales():

    print("Creating Daily Sales...")

    transactions = pd.read_sql(
        "SELECT * FROM transactions",
        engine
    )

    transactions["transaction_date"] = pd.to_datetime(
        transactions["transaction_date"]
    )

    daily = (
        transactions
        .groupby(
            transactions["transaction_date"].dt.date
        )
        .agg(
            Revenue=("total_amount", "sum"),
            Orders=("transaction_id", "count")
        )
        .reset_index()
    )

    daily.to_sql(
        "daily_sales",
        engine,
        if_exists="replace",
        index=False
    )

    print("✓ daily_sales created.")


# ============================================================
# MAIN
# ============================================================

def main():

    create_sales_summary()

    create_store_summary()

    create_daily_sales()

    print("\n====================================")
    print("Data Warehouse Created Successfully!")
    print("====================================")


if __name__ == "__main__":
    main()