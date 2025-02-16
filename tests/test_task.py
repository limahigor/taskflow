import sys
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from server import app, Base, get_db

TEST_DATABASE_URL = "sqlite:///./test_db.sqlite3"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

client = TestClient(app)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function", autouse=True)
def reset_database():
    """ Apaga e recria o banco antes de cada teste """
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    
@pytest.fixture
def task_data():
    return {"title": "Simple task", "description": "A simple test task", "user_id": "1"}

@pytest.fixture
def task_missing_data():
    return {"description": "A simple test task", "user_id": "1"}

@pytest.fixture
def user_data():
    return {"name": "Higor", "email": "higor@higor.com"}

@pytest.fixture
def expected_response():
    return {
                'id': 1, 
                'title': 'Simple task', 
                'description': 'A simple test task', 
                'status': 'pendent', 
                'user': {
                    'id': 1, 
                    'name': 'Higor', 
                    'email': 'higor@higor.com'
                }
            }
    
@pytest.fixture
def created_task(user_data, task_data):
    user_response = client.post("/users/", json=user_data)
    assert user_response.status_code == 200

    response = client.post("/tasks/", json=task_data)
    assert response.status_code == 200
    
@pytest.fixture
def users_data():
    """ Retorna uma lista de 2 usuários para criação """
    return [
        {"name": "User 1", "email": "user1@example.com"},
        {"name": "User 2", "email": "user2@example.com"}
    ]

@pytest.fixture
def tasks_data():
    return [
        {"title": "Task 1", "description": "Description 1", "user_id": 1},
        {"title": "Task 2", "description": "Description 2", "user_id": 1},
        {"title": "Task 3", "description": "Description 3", "user_id": 2}
    ]
    
class TestTasksPostRoute:
    def test_create_task(self, task_data, user_data, expected_response):
        """ Should create Task with correct data """
        response = client.post("/users/", json=user_data)
        assert response.status_code == 200
        
        response = client.post("/tasks/", json=task_data)
        
        assert response.status_code == 200
        assert response.json() == expected_response
        
    def test_create_task_user_not_exists(self, task_data):
        """ Should returns 400 if user not exists """       
        response = client.post("/tasks/", json=task_data)
        
        assert response.status_code == 400
        
    def test_create_user_missing_data(self, task_missing_data):
        """ Should return 400 if missing data is provided """
        response = client.post("/tasks/", json=task_missing_data)
        assert response.status_code == 400
        
class TestTasksPutRoute:
    def test_update_task_status(self, created_task):
       
        """ Should update task status successfully """
        response = client.put("/tasks/1", json={"status": 1})
        
        assert response.status_code == 200
        assert response.json()["status"] == "on going"
        
    def test_update_task_invalid_status(self, created_task):
        """ Should return 400 if invalid status is provided """
        
        response = client.put("/tasks/1", json={"status": 5})
        
        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid status code"

    def test_update_task_not_found(self):
        """ Should return 400 if task does not exist """
        response = client.put("/tasks/99999", json={"status": 1})
        
        assert response.status_code == 400
        assert response.json()["detail"] == "Task not found"
        
    def test_update_task_missing_data(self):
        """ Should return 400 if missing data is provided """
        response = client.put("/tasks/1")
        assert response.status_code == 400
        
class TestTasksGetRout:
    def test_get_tasks(self, users_data, tasks_data):
        """ Should create users and tasks, then list all tasks correctly """

        created_users = []
        for user in users_data:
            response = client.post("/users/", json=user)
            assert response.status_code == 200
            created_users.append(response.json())
        
        created_tasks = []
        for task in tasks_data:
            response = client.post("/tasks/", json=task)
            assert response.status_code == 200
            created_tasks.append(response.json())

        response = client.get("/tasks/")
        assert response.status_code == 200
        tasks_response = response.json()

        assert len(tasks_response) == len(tasks_data)

        tasks_expected = [
            {
                "title": task["title"],
                "description": task["description"],
                "status": "pendent",
                "user": {
                    "name": created_users[0]["name"] if i < 2 else created_users[1]["name"],
                    "email": created_users[0]["email"] if i < 2 else created_users[1]["email"]
                }
            }
            for i, task in enumerate(tasks_data)
        ]

        tasks_returned = [
            {
                "title": task["title"],
                "description": task["description"],
                "status": task["status"],
                "user": {
                    "name": task["user"]["name"],
                    "email": task["user"]["email"]
                }
            }
            for task in tasks_response
        ]

        assert sorted(tasks_expected, key=lambda x: x["title"]) == sorted(tasks_returned, key=lambda x: x["title"])
                