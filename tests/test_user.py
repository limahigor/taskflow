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

class TestUserRoutes:
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