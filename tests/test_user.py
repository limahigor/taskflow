import sys
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from server import app, Base, SessionLocal, get_db

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
def user_data():
    return {"name": "Higor", "email": "higor@higor.com"}

@pytest.fixture
def missing_user_data():
    return {"name": "Higor"}

@pytest.fixture
def user_create_get_data():
    return [
        { "name": "higor1","email": "higor1@higor.com" },
        { "name": "higor2", "email": "higor2@higor.com" },
        { "name": "higor3", "email": "higor3@higor.com" }
    ]

class TestUserPostRoute:
    def test_create_user(self, user_data):
        """ Should create user with correct data """
        response = client.post("/users/", json=user_data)
        assert response.status_code == 200
        assert response.json() == user_data

    def test_create_user_missing_data(self, missing_user_data):
        """ Should return 400 if missing data is provided """
        response = client.post("/users/", json=missing_user_data)
        assert response.status_code == 400
    
    def test_create_duplicate_user(self, user_data):
        """ Should return 400 if User already exists """
        client.post("/users/", json=user_data)
        response = client.post("/users/", json=user_data)
        assert response.status_code == 400
        
class TestUserGetRoutes:
    def test_get_user(self, user_create_get_data):
        """ Should return all users list """
        
        for user in user_create_get_data:
            response = client.post("/users/", json=user)
            assert response.status_code == 200

        response = client.get("/users/")
        assert response.status_code == 200

        users_response = response.json()
        print(users_response)
        assert len(users_response) == 3
        
        users_returned = [{"name": u["name"], "email": u["email"]} for u in users_response]
        assert sorted(user_create_get_data, key=lambda x: x["email"]) == sorted(users_returned, key=lambda x: x["email"])