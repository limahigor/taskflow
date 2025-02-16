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
    
class TaskUpdate(BaseModel):
    status: int
    
STATUS_MAP = {
    0: "pendent",
    1: "on going",
    2: "completed"
}
    
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
    finally:
        db.close()
        
    return user

@app.get("/users/", response_model=List[UserResponse])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    db.close()
    return users

@app.post("/tasks/", response_model=TaskResponse)
async def create_task(request: Request, db: Session = Depends(get_db)):
    try:
        task_data = await request.json()
        print(task_data)
        task = TaskCreate(**task_data)
        print(task)
        
        user = db.query(User).filter(User.id == task.user_id).first()
        
        if not user:
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
    except ValidationError:
        raise HTTPException(status_code=400, detail="Invalid request data")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500)
    finally:
        db.close()
        
    return TaskResponse(id=db_task.id, title=db_task.title, description=db_task.description, status=db_task.status, user=user_response)

@app.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task_status(task_id: int, request: Request, db: Session = Depends(get_db)):
    try:
        task_data = await request.json()
        task_update = TaskUpdate(**task_data)
        db_task = db.query(Task).filter(Task.id == task_id).first()
        
        if not db_task:
            raise ValueError("Task not found")

        if task_update.status not in STATUS_MAP:
            raise ValueError("Invalid status code")

        db_task.status = STATUS_MAP[task_update.status]
        db.commit()
        db.refresh(db_task)

        return db_task
    except ValidationError:
        raise HTTPException(status_code=400, detail="Invalid request data")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
@app.get("/tasks/", response_model=List[TaskResponse])
def list_tasks(db: Session = Depends(get_db)):
    tasks = db.query(Task).all()
    task_list = [TaskResponse(id=t.id, title=t.title, description=t.description, status=t.status, user=UserResponse(id=t.user_id,name=t.user.name, email=t.user.email)) for t in tasks]
    db.close()
    return task_list