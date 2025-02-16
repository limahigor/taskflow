from fastapi import FastAPI, HTTPException, Request, Depends
from pydantic import BaseModel, ValidationError
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session
from sqlalchemy.exc import IntegrityError
from typing import List

DATABASE_URL = "sqlite:///db.sqlite3"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)

Base.metadata.create_all(bind=engine)
app = FastAPI()

class UserCreate(BaseModel):
    name: str
    email: str
    
class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/users/", response_model=UserCreate)
async def create_user(request: Request, db: Session = Depends(get_db)):
    try:
        user_data = await request.json()
        user = UserCreate(**user_data)
        
        db_user = User(name=user.name, email=user.email)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    except ValidationError:
        raise HTTPException(status_code=400, detail="Invalid request data")
    except IntegrityError:
        raise HTTPException(status_code=400, detail="User already exists")
    
    return user

@app.get("/users/", response_model=List[UserResponse])
def list_users():
    db = SessionLocal()
    users = db.query(User).all()
    db.close()
    return users