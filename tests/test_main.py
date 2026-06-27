"""Tests de los endpoints con pytest + TestClient."""
import pytest
from fastapi.testclient import TestClient

from app import storage
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def _reset_storage():
    """Reinicia el almacenamiento en memoria antes de cada test."""
    storage.reset()
    yield
    storage.reset()


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_root_info():
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["links"]["health"] == "/health"


def test_items_empty():
    resp = client.get("/items")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_item_valid():
    resp = client.post("/items", json={"name": "Teclado", "price": 25.5})
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] == 1
    assert body["name"] == "Teclado"
    assert body["price"] == 25.5

    # Aparece en el listado
    listed = client.get("/items").json()
    assert len(listed) == 1
    assert listed[0]["name"] == "Teclado"


@pytest.mark.parametrize(
    "payload",
    [
        {"name": "", "price": 10},      # nombre vacio
        {"name": "X", "price": 0},       # precio no positivo
        {"name": "X", "price": -5},      # precio negativo
        {"price": 10},                    # falta nombre
        {"name": "X"},                    # falta precio
    ],
)
def test_create_item_invalid(payload):
    resp = client.post("/items", json=payload)
    assert resp.status_code == 422


def test_admin_status():
    resp = client.get("/admin/status")
    assert resp.status_code == 200
    body = resp.json()
    assert "uptime_seconds" in body
    assert "items_count" in body
