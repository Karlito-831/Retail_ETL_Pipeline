from faker import Faker
import pandas as pd
import random
from pathlib import Path

# Initialize Faker
fake = Faker()

# -----------------------------
# Configuration
# -----------------------------
NUM_CUSTOMERS = 1000
NUM_PRODUCTS = 500
NUM_STORES = 20
NUM_TRANSACTIONS = 100000

CATEGORIES = [
    "Electronics",
    "Clothing",
    "Home",
    "Sports",
    "Beauty",
    "Kitchen"
]

STORE_CITIES = [
    "Johannesburg",
    "Pretoria",
    "Cape Town",
    "Durban",
    "Bloemfontein",
    "Polokwane",
    "Nelspruit",
    "Kimberley"
]

# Create output directory if it doesn't exist
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)


# -----------------------------
# Generate Customers
# -----------------------------
def generate_customers():
    customers = []

    for _ in range(NUM_CUSTOMERS):
        customers.append({
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": fake.unique.email(),
            "phone": fake.phone_number(),
            "city": fake.city(),
            "country": "South Africa",
            "registration_date": fake.date_between(
                start_date="-5y",
                end_date="today"
            )
        })

    return pd.DataFrame(customers)


# -----------------------------
# Generate Products
# -----------------------------
def generate_products():
    products = []

    for _ in range(NUM_PRODUCTS):
        products.append({
            "product_name": fake.word().title(),
            "category": random.choice(CATEGORIES),
            "price": round(random.uniform(50, 5000), 2),
            "stock_quantity": random.randint(10, 500)
        })

    return pd.DataFrame(products)


# -----------------------------
# Generate Stores
# -----------------------------
def generate_stores():
    stores = []

    for i in range(NUM_STORES):
        stores.append({
            "store_name": f"Retail Store {i + 1}",
            "city": random.choice(STORE_CITIES),
            "country": "South Africa"
        })

    return pd.DataFrame(stores)


# -----------------------------
# Generate Transactions
# -----------------------------
def generate_transactions():
    transactions = []

    for _ in range(NUM_TRANSACTIONS):
        quantity = random.randint(1, 5)
        price = round(random.uniform(50, 5000), 2)

        transactions.append({
            "customer_id": random.randint(1, NUM_CUSTOMERS),
            "product_id": random.randint(1, NUM_PRODUCTS),
            "store_id": random.randint(1, NUM_STORES),
            "quantity": quantity,
            "total_amount": round(quantity * price, 2),
            "transaction_date": fake.date_time_between(
                start_date="-2y",
                end_date="now"
            )
        })

    return pd.DataFrame(transactions)


# -----------------------------
# Main Program
# -----------------------------
if __name__ == "__main__":

    print("Generating customers...")
    customers = generate_customers()

    print("Generating products...")
    products = generate_products()

    print("Generating stores...")
    stores = generate_stores()

    print("Generating transactions...")
    transactions = generate_transactions()

    customers.to_csv(RAW_DATA_DIR / "customers.csv", index=False)
    products.to_csv(RAW_DATA_DIR / "products.csv", index=False)
    stores.to_csv(RAW_DATA_DIR / "stores.csv", index=False)
    transactions.to_csv(RAW_DATA_DIR / "transactions.csv", index=False)

    print("\n====================================")
    print("Data generation completed successfully!")
    print("====================================")
    print(f"Customers:     {len(customers):,}")
    print(f"Products:      {len(products):,}")
    print(f"Stores:        {len(stores):,}")
    print(f"Transactions:  {len(transactions):,}")
    print(f"\nCSV files saved to:\n{RAW_DATA_DIR}")