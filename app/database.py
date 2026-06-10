import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Strike(Base):
    __tablename__ = "strikes"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True)
    distance = Column(Integer, nullable=False)  # Distance in km (0 - 40)
    intensity = Column(Integer, nullable=False)  # Raw intensity value (energy)

class SensorConfig(Base):
    __tablename__ = "sensor_config"

    key = Column(String(100), primary_key=True, index=True)
    value = Column(String(500), nullable=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db(db_engine=engine):
    Base.metadata.create_all(bind=db_engine)

# Helper function to get config value
def get_config_val(db, key: str, default: str = "") -> str:
    cfg = db.query(SensorConfig).filter(SensorConfig.key == key).first()
    return cfg.value if cfg else default

# Helper function to set config value
def set_config_val(db, key: str, value: str):
    cfg = db.query(SensorConfig).filter(SensorConfig.key == key).first()
    if cfg:
        cfg.value = str(value)
    else:
        cfg = SensorConfig(key=key, value=str(value))
        db.add(cfg)
    db.commit()
