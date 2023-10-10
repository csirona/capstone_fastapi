from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Import your generated models
from db import Base, User, Wallet, Card, Car, ParkingHistory

# Create an SQLAlchemy engine and session
DATABASE_URL = "postgresql+psycopg2://parking:passwordpsql@localhost/dbparking"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Print documentation
def print_table_documentation(table):
    print(f"## {table.__tablename__} Table")
    print()
    print("Column | Type | Description")
    print("--- | --- | ---")
    for column in table.__table__.columns:
        print(
            f"{column.name} | {column.type} | Description of {column.name} column"
        )
    print()

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    tables = [User, Wallet, Card, Car, ParkingHistory]
    for table in tables:
        print_table_documentation(table)

