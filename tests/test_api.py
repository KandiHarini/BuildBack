import os
import tempfile
import pytest
from app import app
from models import db

@pytest.fixture()
def client():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///" + path,
        SECRET_KEY="test-secret"
    )
    with app.app_context():
        db.drop_all()
        db.create_all()
    with app.test_client() as client:
        yield client
    with app.app_context():
        db.session.remove()
        db.drop_all()
    os.unlink(path)

def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json["status"] == "ok"

def test_register_login_and_material(client):
    response = client.post("/api/register", json={
        "name": "Provider", "email": "provider@example.com",
        "password": "password123", "role": "provider"
    })
    assert response.status_code == 201
    response = client.post("/api/login", json={
        "email": "provider@example.com", "password": "password123"
    })
    assert response.status_code == 200
    response = client.post("/api/materials", json={
        "title": "Unused bricks", "category": "Bricks", "quantity": 100,
        "unit": "pieces", "condition": "Good", "location": "Hyderabad",
        "price": 0, "is_free": True
    })
    assert response.status_code == 201
    response = client.get("/api/materials")
    assert response.status_code == 200
    assert len(response.json) == 1
