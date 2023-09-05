from fastapi import FastAPI, HTTPException, Depends, Response
from sqlalchemy.orm import Session
from db import connect_to_db, disconnect_from_db, SessionLocal, User, Wallet, Card, Car,fetch_user_from_db, ParkingHistory,get_car
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from db import SessionLocal
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

app = FastAPI()

origins = ["*"]  # Add your frontend URLs

# JWT configuration
SECRET_KEY = "9a906627c7d4dac428f7ca952626b15e4cae78aa8f784527637f46ed5aba1eaa"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic model for creating a user
class UserCreate(BaseModel):
    username: str
    email: str
    hashed_password: str


# Token model
class Token(BaseModel):
    access_token: str
    token_type: str

# Pydantic model for creating a wallet
class WalletCreate(BaseModel):
    user_id: int
    balance: float

# Pydantic model for wallet response
class WalletResponse(BaseModel):
    id: int
    user_id: int
    balance: float

# Pydantic model for creating a card
class CardCreate(BaseModel):
    user_id: int
    card_number: str

# Pydantic model for card response
class CardResponse(BaseModel):
    id: int
    user_id: int
    card_number: str

# Pydantic model for creating a car
class CarCreate(BaseModel):
    user_id: int
    license_plate: str

# Pydantic model for car response
class CarResponse(BaseModel):
    id: int
    user_id: int
    license_plate: str
    

# User authentication
def authenticate_user(db_user: User, password: str):
    if not pwd_context.verify(password, db_user.hashed_password):
        return False
    return True

# Create a JWT token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        # Fetch user from the database based on the username and return it
        db_user = fetch_user_from_db(username)  # Implement this function
        if db_user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return db_user
    except JWTError:
        raise HTTPException(status_code=401, detail="Token validation failed")
# Function to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Login route
@app.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    username = form_data.username
    password = form_data.password
    db_user = fetch_user_from_db(username, db)  # Pass the session as well
    
    if db_user and pwd_context.verify(password, db_user.hashed_password):
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

# Protected resource
@app.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    return {"message": "This is a protected resource"}


@app.on_event("startup")
async def startup():
    await connect_to_db()

@app.on_event("shutdown")
async def shutdown():
    await disconnect_from_db()

# Create a new user
@app.post("/users/")
async def create_user(user_data: UserCreate):
    try:
        db = SessionLocal()
        hashed_password = pwd_context.hash(user_data.hashed_password)
        new_user = User(username=user_data.username, email=user_data.email, hashed_password=hashed_password)
        db.add(new_user)
        db.commit()
        db.close()
        return {"message": "User created successfully"}
    except Exception as e:
        return {"message": f"Error creating user: {str(e)}"}

# Pydantic model for user response
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    hashed_password : str

# Add a route to list all users
@app.get("/users/", response_model=List[UserResponse])  # Use the UserResponse model
async def list_users():
    db = SessionLocal()
    users = db.query(User).all()
    db.close()
    return users

# Get a user by ID
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    db.close()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Create a new wallet
@app.post("/wallets/")
async def create_wallet(wallet_data: WalletCreate):
    try:
        db = SessionLocal()
        new_wallet = Wallet(user_id=wallet_data.user_id, balance=wallet_data.balance)
        db.add(new_wallet)
        db.commit()
        db.close()
        return {"message": "Wallet created successfully"}
    except Exception as e:
        return {"message": f"Error creating wallet: {str(e)}"}

# Get a wallet by ID
@app.get("/wallets/{wallet_id}")
async def get_wallet(wallet_id: int):
    db = SessionLocal()
    wallet = db.query(Wallet).filter(Wallet.id == wallet_id).first()
    db.close()
    if wallet is None:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return wallet

# Create a new card
@app.post("/cards/")
async def create_card(card_data: CarCreate):
    db = SessionLocal()
    new_card = Card(user_id=card_data.user_id, card_number=card_data.card_number)
    db.add(new_card)
    db.commit()
    db.close()
    return {"message": "Card created successfully"}

# Get a card by ID
@app.get("/cards/{card_id}")
async def get_card(card_id: int):
    db = SessionLocal()
    card = db.query(Card).filter(Card.id == card_id).first()
    db.close()
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")
    return card

@app.post("/cars/")
async def create_car(car_data: CarCreate):
    try:
        db = SessionLocal()
        new_car = Car(user_id=car_data.user_id, license_plate=car_data.license_plate)
        db.add(new_car)
        db.commit()
        db.close()
        return {"message": "Car created successfully"}
    except Exception as e:
        return {"message": f"Error creating car: {str(e)}"}

# Get a car by ID
@app.get("/cars/{user_id}")
async def get_car(user_id: int):
    db = SessionLocal()
    cars = db.query(Car).filter(Car.user_id == user_id).all()
    db.close()
    if cars is None:
        raise HTTPException(status_code=404, detail="Car not found")
    return cars

class ParkingHistoryCreate(BaseModel):
    car_id: int

class ParkingHistoryResponse(BaseModel):
    id: int
    date: Optional[datetime]

@app.post("/parking-history/", response_model=dict)
async def create_parking_history(parking_history_data: ParkingHistoryCreate, response: Response):
    db = SessionLocal()
    try:
        car = db.query(Car).filter(Car.id == parking_history_data.car_id).first()
        if not car:
            raise HTTPException(status_code=404, detail="Car not found")

        new_parking_history = ParkingHistory(car_id=parking_history_data.car_id)
        db.add(new_parking_history)
        db.commit()
        db.refresh(new_parking_history)

        return {"message": "Parking history entry created successfully"}

    except Exception as e:
        response.status_code = 500
        return {"message": f"Error creating parking history: {str(e)}"}
    finally:
        db.close()


@app.get("/parking-history/{car_id}", response_model=List[ParkingHistoryResponse])
async def get_parking_history(car_id: int):
    db = SessionLocal()
    try:
        car = db.query(Car).filter(Car.id == car_id).first()
        if not car:
            raise HTTPException(status_code=404, detail="Car not found")

        parking_history = db.query(ParkingHistory).filter(ParkingHistory.car_id == car_id).all()
        return [{"id": entry.id, "date": entry.date} for entry in parking_history]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching parking history: {str(e)}")
    finally:
        db.close()





if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
