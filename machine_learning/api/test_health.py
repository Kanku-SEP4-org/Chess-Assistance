import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    from main import app

    return TestClient(app)


class TestHealthLiveness:
    def test_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestHealthReady:
    def test_reports_model_status(self, client):
        resp = client.get("/health/ready")
        body = resp.json()
        assert "models" in body
        for key in ("winrate", "angriness", "accuracy_predictor"):
            assert key in body["models"]

    def test_degraded_when_db_not_configured(self, client):
        with patch("main.DATABASE_URL", ""):
            resp = client.get("/health/ready")
        assert resp.json()["database"] == "not_configured"
        assert resp.status_code == 503
        assert resp.json()["status"] == "degraded"

    @pytest.mark.skipif(
        not os.getenv("DATABASE_URL"),
        reason="DATABASE_URL not set — skip real DB test",
    )
    def test_database_ok_with_real_connection(self, client):
        resp = client.get("/health/ready")
        body = resp.json()
        assert body["database"] == "ok"

    def test_database_error_with_bad_url(self, client):
        with patch("main.DATABASE_URL", "postgresql://bad:bad@localhost:19999/nope"):
            resp = client.get("/health/ready")
        body = resp.json()
        assert body["database"].startswith("error:")
        assert resp.status_code == 503
