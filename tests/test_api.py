import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from app.database import Base, get_db, Strike
from app.hardware import sensor_hardware, gpio_manager

# Setup separate SQLite db for API testing
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Database Session Fixture
@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

# TestClient Fixture
@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
            
    # Override FastAPI dependency
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

def test_get_recent_strikes_empty(client):
    response = client.get("/api/strikes/recent")
    assert response.status_code == 200
    assert response.json() == []

def test_get_recent_strikes_with_data(client, db_session):
    # Seed data
    s1 = Strike(distance=5, intensity=200)
    s2 = Strike(distance=10, intensity=300)
    db_session.add_all([s1, s2])
    db_session.commit()

    response = client.get("/api/strikes/recent")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["distance"] == 10  # ordered descending by timestamp
    assert data[1]["distance"] == 5

def test_get_strike_stats(client, db_session):
    # Seed data
    s1 = Strike(distance=5, intensity=200)
    s2 = Strike(distance=15, intensity=400)
    db_session.add_all([s1, s2])
    db_session.commit()

    response = client.get("/api/strikes/stats")
    assert response.status_code == 200
    stats = response.json()
    assert stats["amount_24h"] == 2
    assert stats["amount_7d"] == 2
    assert stats["avg_distance"] == 10.0
    assert stats["avg_intensity"] == 300.0
    assert stats["closest_distance"] == 5

def test_get_sensor_status_defaults(client):
    response = client.get("/api/sensor/status")
    assert response.status_code == 200
    status = response.json()
    assert status["capacitance"] == 96
    assert status["location"] == 0
    assert status["disturber"] == 1

def test_update_sensor_config(client):
    payload = {
        "capacitance": 88,
        "location": 1,
        "disturber": 0,
        "noise_floor": 4,
        "watchdog": 3,
        "spike_rejection": 5,
        "display_active_start": 9,
        "display_active_end": 19,
        "telegram_enabled": True,
        "telegram_token": "token123",
        "telegram_chat_id": "chat123"
    }
    response = client.post("/api/sensor/config", json=payload)
    assert response.status_code == 200
    status = response.json()
    assert status["capacitance"] == 88
    assert status["location"] == 1
    assert status["disturber"] == 0
    assert status["noise_floor"] == 4
    assert status["watchdog"] == 3
    assert status["spike_rejection"] == 5
    assert status["display_active_start"] == 9
    assert status["display_active_end"] == 19
    assert status["telegram_enabled"] is True

def test_simulate_strike_endpoint(client):
    payload = {"distance": 25, "intensity": 750}
    response = client.post("/api/strikes/simulate", json=payload)
    assert response.status_code == 200
    strike = response.json()
    assert strike["distance"] == 25
    assert strike["intensity"] == 750
    assert "timestamp" in strike
    assert "id" in strike
