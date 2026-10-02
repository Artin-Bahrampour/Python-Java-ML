from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import get_settings
from app.models import Base

def build_engine():
    url = get_settings().database_url
    if url.startswith("sqlite:///"):
        Path(url.removeprefix("sqlite:///" )).parent.mkdir(parents=True, exist_ok=True)
    return create_engine(url, connect_args={"check_same_thread": False} if url.startswith("sqlite") else {})
engine = build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
def init_db(): Base.metadata.create_all(bind=engine)
def get_session():
    session = SessionLocal()
    try: yield session
    finally: session.close()
