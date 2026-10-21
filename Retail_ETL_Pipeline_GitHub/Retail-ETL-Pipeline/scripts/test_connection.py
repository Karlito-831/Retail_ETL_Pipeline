from database import get_engine

try:
    engine = get_engine()

    with engine.connect() as connection:
        print("Connected to PostgreSQL successfully!")

except Exception as e:
    print("Connection failed.")
    print(e)