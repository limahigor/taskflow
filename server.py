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
    tasks = relationship("Task", back_populates="user")
    
class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, index=True)
    description = Column(String)
    status = Column(String, default="pendent")
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="tasks")

Base.metadata.create_all(bind=engine)
app = FastAPI()

class UserCreate(BaseModel):
    name: str
    email: str
    
class UserResponse(BaseModel):
    id: int
    name: str
    email: str    

class TaskCreate(BaseModel):
    title: str
    description: str
    user_id: int

class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str
    user: UserResponse
    
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
    except Exception:
        raise HTTPException(status_code=500)
        
    return user

@app.get("/users/", response_model=List[UserResponse])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    db.close()
    return users

@app.post("/tasks/", response_model=TaskResponse)
async def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.id == task.user_id).first()
        
        if not user:
            db.close()
            raise ValueError("User not exists")
        
        db_task = Task(
            title=task.title,
            description=task.description,
            status="pendent",
            user_id=task.user_id
        )
        
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        
        user_response = UserResponse(id=user.id, name=user.name, email=user.email)

        db.close()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500)
        
    return TaskResponse(id=db_task.id, title=db_task.title, description=db_task.description, status=db_task.status, user=user_response)