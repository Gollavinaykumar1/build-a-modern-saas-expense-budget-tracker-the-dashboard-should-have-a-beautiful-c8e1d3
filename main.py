# main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date
from typing import List, Optional
import os
from dotenv import load_dotenv

# Security & Hashing
from jose import JWTError, jwt
from passlib.context import CryptContext

# Pydantic models for request/response
from pydantic import BaseModel, Field, condecimal

# Database setup and models
from database import SessionLocal, engine, Base, create_tables
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

# Load environment variables
load_dotenv()

# --- Database Models ---
class DBUser(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    expenses = relationship("DBExpense", back_populates="owner")

class DBExpense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)
    expense_date = Column(DateTime, default=datetime.utcnow)
    is_subscription = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("DBUser", back_populates="expenses")

# --- FastAPI App Initialization ---
app = FastAPI(
    title="SaaS Expense & Budget Tracker Backend",
    description="A modern backend for managing expenses, budgets, and user authentication.",
    version="1.0.0",
)

# Create database tables on startup
@app.on_event("startup")
def on_startup():
    create_tables()
    print("Database tables ensured to be created.")

# --- Security Configuration ---
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key") # Change this in production!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- Pydantic Schemas (Request/Response Models) ---
class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class ExpenseBase(BaseModel):
    amount: condecimal(max_digits=10, decimal_places=2) # e.g., 12345678.99
    category: str = Field(..., example="Groceries")
    description: Optional[str] = Field(None, example="Weekly shopping at Trader Joe's")
    expense_date: Optional[datetime] = Field(None, description="Defaults to current UTC time if not provided.")
    is_subscription: bool = False

class ExpenseCreate(ExpenseBase):
    pass # Same as Base for creation

class Expense(ExpenseBase):
    id: int
    owner_id: int
    expense_date: datetime # Required for response
    class Config:
        from_attributes = True

class KPIResponse(BaseModel):
    total_balance: condecimal(max_digits=12, decimal_places=2) = Field(..., description="Total aggregate of all expenses (negative value)")
    monthly_spend: condecimal(max_digits=12, decimal_places=2) = Field(..., description="Total expenses for the current month")
    largest_expense: condecimal(max_digits=10, decimal_places=2) = Field(..., description="Amount of the single largest expense")
    active_subscriptions: int = Field(..., description="Count of distinct categories marked as subscriptions")


# --- Dependency for Database Session ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Dependency for Current User Authentication ---
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = db.query(DBUser).filter(DBUser.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

# --- CRUD Operations for Users ---
def get_user_by_username(db: Session, username: str):
    return db.query(DBUser).filter(DBUser.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(DBUser).filter(DBUser.email == email).first()

def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = DBUser(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- API Endpoints ---

@app.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    """
    db_user_by_username = get_user_by_username(db, username=user.username)
    if db_user_by_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
    db_user_by_email = get_user_by_email(db, email=user.email)
    if db_user_by_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    return create_user(db=db, user=user)

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Authenticate user and return an access token.
    """
    user = get_user_by_username(db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: DBUser = Depends(get_current_user)):
    """
    Get the current authenticated user's details.
    """
    return current_user

@app.post("/expenses", response_model=Expense, status_code=status.HTTP_201_CREATED)
async def create_expense(
    expense: ExpenseCreate,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a new expense for the current user.
    """
    db_expense = DBExpense(
        amount=float(expense.amount), # Convert Pydantic Decimal to float for DB
        category=expense.category,
        description=expense.description,
        expense_date=expense.expense_date if expense.expense_date else datetime.utcnow(),
        is_subscription=expense.is_subscription,
        owner_id=current_user.id
    )
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense

@app.get("/expenses", response_model=List[Expense])
async def read_expenses(
    skip: int = 0,
    limit: int = 100,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve all past transactions for the current user.
    """
    expenses = db.query(DBExpense).filter(DBExpense.owner_id == current_user.id).offset(skip).limit(limit).order_by(DBExpense.expense_date.desc()).all()
    return expenses

@app.get("/expenses/kpis", response_model=KPIResponse)
async def get_kpis(
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve key performance indicator (KPI) metrics for the current user.
    Includes Total Balance, Monthly Spend, Largest Expense, and Active Subscriptions.
    """
    all_expenses = db.query(DBExpense).filter(DBExpense.owner_id == current_user.id).all()

    # Initialize KPI values
    total_balance = 0.0
    monthly_spend = 0.0
    largest_expense = 0.0
    active_subscriptions = set() # Using a set to count distinct categories

    current_month = date.today().month
    current_year = date.today().year

    for expense in all_expenses:
        # Total Balance (representing total outflow)
        total_balance -= expense.amount

        # Monthly Spend
        if expense.expense_date.month == current_month and expense.expense_date.year == current_year:
            monthly_spend += expense.amount

        # Largest Expense
        if expense.amount > largest_expense:
            largest_expense = expense.amount
        
        # Active Subscriptions
        if expense.is_subscription:
            active_subscriptions.add(expense.category.lower()) # Case-insensitive counting

    return KPIResponse(
        total_balance=total_balance,
        monthly_spend=monthly_spend,
        largest_expense=largest_expense,
        active_subscriptions=len(active_subscriptions)
    )