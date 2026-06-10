import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, Strike, SensorConfig, get_config_val, set_config_val

# Setup in-memory SQLite database for testing
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_strike_creation(db_session):
    # Test inserting a strike record
    strike = Strike(distance=12, intensity=450)
    db_session.add(strike)
    db_session.commit()
    db_session.refresh(strike)

    assert strike.id is not None
    assert strike.distance == 12
    assert strike.intensity == 450
    assert strike.timestamp is not None

def test_config_helper_functions(db_session):
    # Test setting and getting configuration values
    set_config_val(db_session, "test_key", "test_value")
    
    # Check database write
    cfg = db_session.query(SensorConfig).filter(SensorConfig.key == "test_key").first()
    assert cfg is not None
    assert cfg.value == "test_value"

    # Get config value using helper
    val = get_config_val(db_session, "test_key", default="fallback")
    assert val == "test_value"

    # Test default fallback value for non-existent key
    fallback_val = get_config_val(db_session, "non_existent_key", default="fallback")
    assert fallback_val == "fallback"

def test_config_override(db_session):
    # Test overriding an existing configuration key
    set_config_val(db_session, "mode", "indoor")
    assert get_config_val(db_session, "mode") == "indoor"

    set_config_val(db_session, "mode", "outdoor")
    assert get_config_val(db_session, "mode") == "outdoor"
