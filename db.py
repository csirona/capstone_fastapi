from sqlalchemy import create_engine, Column, Integer, DateTime,String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from databases import Database
from sqlalchemy.orm import relationship
from passlib.context import CryptContext
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

DATABASE_URL = "mysql+mysqlconnector://root:passwordmysql@localhost/parking_app_db"

database = Database(DATABASE_URL)
Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")





class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), index=True)
    email = Column(String(255))
    # Establish a bidirectional one-to-many relationship with cars
    cars = relationship("Car", back_populates="user")
    hashed_password = Column(String(255))  # Add this field for hashed passwords

class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    balance = Column(Float)

class Card(Base):
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    card_number = Column(String(255))

class Car(Base):
    __tablename__ = "cars"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    license_plate = Column(String(255))
    # Establish a many-to-one relationship with users
    user = relationship("User", back_populates="cars")
    parking_history = relationship("ParkingHistory", back_populates="car")

class ParkingHistory(Base):
    __tablename__ = "parking_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)  # Add autoincrement=True here
    car_id = Column(Integer, ForeignKey("cars.id"))
    date = Column(DateTime(timezone=True), server_default=func.now())

    car = relationship("Car", back_populates="parking_history")


engine = create_engine(DATABASE_URL)
Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def connect_to_db():
    await database.connect()

async def disconnect_from_db():
    await database.disconnect()

def fetch_user_from_db(username: str, session: Session):
    return session.query(User).filter(User.username == username).first()

async def get_car(db: Session, car_id: int):
    return db.query(Car).filter(Car.id == car_id).first()

async def get_parking_history_for_car(db: Session, car_id: int):
    return db.query(ParkingHistory).filter(ParkingHistory.car_id == car_id).all()

