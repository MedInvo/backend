import os

os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

engine = create_engine(
    "sqlite:///./test.db",
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_and_get_product():
    payload = {
        "name": "Paracetamol",
        "category": "Medicine",
        "quantity": 100,
        "price": 25.50,
    }

    response = client.post("/products", json=payload)
    assert response.status_code == 201

    product = response.json()
    assert product["name"] == "Paracetamol"
    assert product["quantity"] == 100

    response = client.get(f"/products/{product['id']}")
    assert response.status_code == 200
    assert response.json()["name"] == "Paracetamol"


def test_missing_product():
    response = client.get("/products/999999")
    assert response.status_code == 404
