"""Tests for api/routes/health.py"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from api.main import app
from api.routes.health import health_check
from core.config import settings
from core.database import get_db


@pytest.mark.unit
class TestHealthCheck:
    """Test suite for the /health endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock async database session whose execute succeeds."""
        db = AsyncMock()
        db.execute = AsyncMock(return_value=None)
        return db

    @pytest.fixture
    def mock_redis_client(self):
        """Create a mock Redis client whose ping succeeds."""
        client = Mock()
        client.ping = Mock(return_value=True)
        return client

    @pytest.mark.asyncio
    async def test_all_dependencies_healthy(self, mock_db, mock_redis_client, monkeypatch):
        """All dependencies healthy should return status 'healthy' with no exception."""
        monkeypatch.setattr(settings, "vector_db_url", "http://localhost:8001")

        with patch("redis.Redis.from_url", return_value=mock_redis_client):
            result = await health_check(db=mock_db)

        assert result["status"] == "healthy"
        assert result["dependencies"]["postgres"] == "healthy"
        assert result["dependencies"]["redis"] == "healthy"
        assert result["dependencies"]["vector_db"] == "healthy"

    @pytest.mark.asyncio
    async def test_postgres_failure_marks_unhealthy_and_raises_503(
        self, mock_redis_client, monkeypatch
    ):
        """A failing Postgres check should raise a 503 with status 'unhealthy'."""
        monkeypatch.setattr(settings, "vector_db_url", "http://localhost:8001")
        db = AsyncMock()
        db.execute = AsyncMock(side_effect=Exception("connection refused"))

        with (
            patch("redis.Redis.from_url", return_value=mock_redis_client),
            pytest.raises(HTTPException) as exc_info,
        ):
            await health_check(db=db)

        assert exc_info.value.status_code == 503
        detail = exc_info.value.detail
        assert detail["status"] == "unhealthy"
        assert detail["dependencies"]["postgres"] == "unhealthy"
        assert detail["dependencies"]["redis"] == "healthy"

    @pytest.mark.asyncio
    async def test_redis_ping_failure_marks_unhealthy_and_raises_503(self, mock_db, monkeypatch):
        """A failing Redis ping should raise a 503 with status 'unhealthy'."""
        monkeypatch.setattr(settings, "vector_db_url", "http://localhost:8001")
        failing_client = Mock()
        failing_client.ping = Mock(side_effect=Exception("redis down"))

        with (
            patch("redis.Redis.from_url", return_value=failing_client),
            pytest.raises(HTTPException) as exc_info,
        ):
            await health_check(db=mock_db)

        assert exc_info.value.status_code == 503
        detail = exc_info.value.detail
        assert detail["status"] == "unhealthy"
        assert detail["dependencies"]["redis"] == "unhealthy"
        assert detail["dependencies"]["postgres"] == "healthy"

    @pytest.mark.asyncio
    async def test_redis_from_url_uses_configured_redis_url(
        self, mock_db, mock_redis_client, monkeypatch
    ):
        """Redis client should be constructed from settings.redis_url."""
        monkeypatch.setattr(settings, "redis_url", "redis://custom-host:6380/2")
        monkeypatch.setattr(settings, "vector_db_url", "http://localhost:8001")

        with patch("redis.Redis.from_url", return_value=mock_redis_client) as mock_from_url:
            await health_check(db=mock_db)

        mock_from_url.assert_called_once_with("redis://custom-host:6380/2", decode_responses=True)

    @pytest.mark.asyncio
    async def test_vector_db_unavailable_when_no_url_configured(
        self, mock_db, mock_redis_client, monkeypatch
    ):
        """An empty vector_db_url should mark vector_db 'unavailable' without failing status."""
        monkeypatch.setattr(settings, "vector_db_url", "")

        with patch("redis.Redis.from_url", return_value=mock_redis_client):
            result = await health_check(db=mock_db)

        assert result["dependencies"]["vector_db"] == "unavailable"
        assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_multiple_dependencies_unhealthy(self, monkeypatch):
        """Both Postgres and Redis failing should still surface a single 'unhealthy' status."""
        monkeypatch.setattr(settings, "vector_db_url", "http://localhost:8001")
        db = AsyncMock()
        db.execute = AsyncMock(side_effect=Exception("connection refused"))
        failing_client = Mock()
        failing_client.ping = Mock(side_effect=Exception("redis down"))

        with (
            patch("redis.Redis.from_url", return_value=failing_client),
            pytest.raises(HTTPException) as exc_info,
        ):
            await health_check(db=db)

        detail = exc_info.value.detail
        assert detail["status"] == "unhealthy"
        assert detail["dependencies"]["postgres"] == "unhealthy"
        assert detail["dependencies"]["redis"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_safety_events_last_hour_defaults_to_zero(
        self, mock_db, mock_redis_client, monkeypatch
    ):
        """safety_events_last_hour should default to 0 (placeholder implementation)."""
        monkeypatch.setattr(settings, "vector_db_url", "http://localhost:8001")

        with patch("redis.Redis.from_url", return_value=mock_redis_client):
            result = await health_check(db=mock_db)

        assert result["safety_events_last_hour"] == 0

    @pytest.mark.asyncio
    async def test_response_includes_iso_timestamp(self, mock_db, mock_redis_client, monkeypatch):
        """Response should include an ISO-formatted timestamp."""
        monkeypatch.setattr(settings, "vector_db_url", "http://localhost:8001")

        with patch("redis.Redis.from_url", return_value=mock_redis_client):
            result = await health_check(db=mock_db)

        # Should not raise - confirms ISO 8601 format.
        from datetime import datetime

        datetime.fromisoformat(result["timestamp"])


@pytest.mark.unit
class TestHealthEndpointIntegration:
    """Integration tests hitting GET /health through the real FastAPI app.

    Unlike TestHealthCheck, these go through routing and FastAPI's dependency
    injection / exception handling, so they catch wiring bugs (wrong path,
    router not mounted, HTTPException not translated into the expected HTTP
    response) that calling health_check() directly cannot.
    """

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def _override_get_db(self, execute_side_effect=None):
        async def override():
            db = AsyncMock()
            db.execute = AsyncMock(side_effect=execute_side_effect)
            yield db

        return override

    @pytest.fixture(autouse=True)
    def cleanup_overrides(self):
        yield
        app.dependency_overrides.pop(get_db, None)

    def test_get_health_returns_200_when_all_dependencies_healthy(self, client, monkeypatch):
        monkeypatch.setattr(settings, "vector_db_url", "http://localhost:8001")
        app.dependency_overrides[get_db] = self._override_get_db()
        healthy_redis = Mock()
        healthy_redis.ping = Mock(return_value=True)

        with patch("redis.Redis.from_url", return_value=healthy_redis):
            response = client.get("/health")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "healthy"
        assert body["dependencies"] == {
            "postgres": "healthy",
            "redis": "healthy",
            "vector_db": "healthy",
        }

    def test_get_health_returns_503_when_postgres_down(self, client, monkeypatch):
        monkeypatch.setattr(settings, "vector_db_url", "http://localhost:8001")
        app.dependency_overrides[get_db] = self._override_get_db(
            execute_side_effect=Exception("connection refused")
        )
        healthy_redis = Mock()
        healthy_redis.ping = Mock(return_value=True)

        with patch("redis.Redis.from_url", return_value=healthy_redis):
            response = client.get("/health")

        assert response.status_code == 503
        detail = response.json()["detail"]
        assert detail["status"] == "unhealthy"
        assert detail["dependencies"]["postgres"] == "unhealthy"

    def test_get_health_returns_503_when_redis_down(self, client, monkeypatch):
        monkeypatch.setattr(settings, "vector_db_url", "http://localhost:8001")
        app.dependency_overrides[get_db] = self._override_get_db()
        failing_redis = Mock()
        failing_redis.ping = Mock(side_effect=Exception("redis down"))

        with patch("redis.Redis.from_url", return_value=failing_redis):
            response = client.get("/health")

        assert response.status_code == 503
        detail = response.json()["detail"]
        assert detail["status"] == "unhealthy"
        assert detail["dependencies"]["redis"] == "unhealthy"
