import os
import tempfile
import pytest
from fastapi.testclient import TestClient

@pytest.fixture()
def client(monkeypatch):
    db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db.close()
    model = tempfile.NamedTemporaryFile(suffix=".joblib", delete=False)
    model.close()
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db.name}")
    monkeypatch.setenv("MODEL_PATH", model.name)

    # Imports are intentionally delayed so environment overrides are applied.
    from app.config import get_settings
    get_settings.cache_clear()
    import app.db as db_module
    db_module.engine = db_module.create_engine(
        f"sqlite:///{db.name}", connect_args={"check_same_thread": False}
    )
    db_module.SessionLocal.configure(bind=db_module.engine)
    db_module.init_db()

    from app.main import app
    yield TestClient(app)

    os.unlink(db.name)
    os.unlink(model.name)
