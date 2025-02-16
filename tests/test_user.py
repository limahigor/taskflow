import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)

@pytest.fixture
def user_data():
    return {"name": "Higor", "email": "higor@higor.com"}

class TestUserRoutes:
    def test_create_user(self, user_data):
        """ Should create user with correct data """
        response = client.post("/users/", json=user_data)
        assert response.status_code == 200
        assert response.json() == user_data

    def test_create_user_missing_email(self, invalid_user_data):
        """ Should return 400 if email is not provided """
        response = client.post("/users/", json=invalid_user_data)
        assert response.status_code == 400