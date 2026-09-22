"""
VCIS 3.0 — Production Configuration & Hardening Security Tests

Validates:
1. CORS:
   - Dynamic parsing from ALLOWED_ORIGINS environment variable.
   - Multiple comma-separated origins with whitespace trimming.
   - Wildcard '*' is filtered/prevented.
   - Sensible local fallback when unset or empty.
2. Database Health Endpoint:
   - Healthy database returns HTTP 200 and 'connected'.
   - Simulated failure returns HTTP 503 and sanitized generic detail.
   - Sensitive details (host, port, credentials, driver errors) are never leaked.
3. JWT Configuration:
   - Configured secret is used correctly.
   - Missing or empty secret raises RuntimeError (no silent fallback).
4. Environment Loading:
   - Backend directory resolution is CWD-independent.
"""

import asyncio
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, "backend")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-unit-tests-32"

from app.core.security import get_jwt_algorithm, get_jwt_secret_key
import app.database as db_module
from app.main import app, get_allowed_origins


class TestProductionConfigurationSecurity(unittest.TestCase):
    """Test suite for production configuration and environment hardening."""

    # -------------------------------------------------------------------------
    # 1. CORS Configuration Tests
    # -------------------------------------------------------------------------

    def test_cors_default_origin(self):
        """Unset ALLOWED_ORIGINS falls back to default local origin."""
        with patch.dict(os.environ, {}, clear=True):
            origins = get_allowed_origins()
            self.assertEqual(origins, ["http://localhost:5173"])

    def test_cors_comma_separated_origins(self):
        """Comma-separated ALLOWED_ORIGINS are trimmed and parsed cleanly."""
        with patch.dict(
            os.environ,
            {"ALLOWED_ORIGINS": "http://localhost:5173, http://localhost:3000, https://vcis.example.com "},
        ):
            origins = get_allowed_origins()
            self.assertEqual(
                origins,
                ["http://localhost:5173", "http://localhost:3000", "https://vcis.example.com"],
            )

    def test_cors_wildcard_rejected(self):
        """Wildcard '*' origin is filtered out and does not weaken credentials."""
        with patch.dict(os.environ, {"ALLOWED_ORIGINS": "*"}):
            origins = get_allowed_origins()
            self.assertNotIn("*", origins)
            self.assertEqual(origins, ["http://localhost:5173"])

    def test_cors_wildcard_in_list_filtered(self):
        """Wildcard '*' mixed with valid origins is stripped."""
        with patch.dict(
            os.environ,
            {"ALLOWED_ORIGINS": "http://localhost:5173, *, https://vcis.example.com"},
        ):
            origins = get_allowed_origins()
            self.assertNotIn("*", origins)
            self.assertEqual(origins, ["http://localhost:5173", "https://vcis.example.com"])

    # -------------------------------------------------------------------------
    # 2. Database Health Endpoint Sanitization Tests
    # -------------------------------------------------------------------------

    def _get(self, path: str):
        scope = {
            "type": "http",
            "method": "GET",
            "path": path,
            "raw_path": path.encode(),
            "query_string": b"",
            "headers": [(b"content-type", b"application/json")],
        }

        status_code = [None]
        response_body = []

        async def receive():
            return {"type": "http.request", "body": b""}

        async def send(message):
            if message["type"] == "http.response.start":
                status_code[0] = message["status"]
            elif message["type"] == "http.response.body":
                response_body.append(message.get("body", b""))

        async def run_app():
            await app(scope, receive, send)

        asyncio.run(run_app())

        body_bytes = b"".join(response_body)
        try:
            data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
        except Exception:
            data = {"raw": body_bytes.decode("utf-8", errors="replace")}

        return status_code[0], data

    def test_health_check_ok(self):
        """Basic /health endpoint returns 200 OK."""
        code, data = self._get("/health")
        self.assertEqual(code, 200)
        self.assertEqual(data.get("status"), "ok")

    def test_database_health_check_connected(self):
        """Healthy database connection returns 200 OK and connected."""
        code, data = self._get("/health/database")
        self.assertEqual(code, 200)
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("database"), "connected")

    def test_database_health_check_error_sanitized(self):
        """Simulated database failure returns 503 and sanitized generic error."""
        sensitive_error_msg = (
            "psycopg.OperationalError: connection to server at 'db.internal.vcis.lan' (10.0.4.15), "
            "port 5432 failed: FATAL: password authentication failed for user 'vcis_admin'"
        )

        with patch("app.main.engine.connect", side_effect=Exception(sensitive_error_msg)):
            code, data = self._get("/health/database")

            # Must return HTTP 503 Service Unavailable
            self.assertEqual(code, 503)
            self.assertEqual(data.get("status"), "unhealthy")
            self.assertEqual(data.get("database"), "disconnected")
            self.assertEqual(data.get("detail"), "Database connection error")

            # Must NOT expose sensitive strings
            response_text = json.dumps(data)
            self.assertNotIn("db.internal.vcis.lan", response_text)
            self.assertNotIn("10.0.4.15", response_text)
            self.assertNotIn("5432", response_text)
            self.assertNotIn("vcis_admin", response_text)
            self.assertNotIn("password authentication failed", response_text)

    # -------------------------------------------------------------------------
    # 3. JWT Configuration Hardening Tests
    # -------------------------------------------------------------------------

    def test_jwt_secret_configured(self):
        """Configured JWT_SECRET_KEY is returned correctly."""
        with patch.dict(os.environ, {"JWT_SECRET_KEY": "super-strong-jwt-secret-key-12345"}):
            secret = get_jwt_secret_key()
            self.assertEqual(secret, "super-strong-jwt-secret-key-12345")

    def test_jwt_secret_missing_raises_runtime_error(self):
        """Missing JWT_SECRET_KEY raises RuntimeError without silent fallback."""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError) as ctx:
                get_jwt_secret_key()
            self.assertIn("JWT_SECRET_KEY", str(ctx.exception))
            self.assertIn("not configured", str(ctx.exception))

    def test_jwt_secret_empty_string_raises_runtime_error(self):
        """Whitespace or empty JWT_SECRET_KEY raises RuntimeError."""
        with patch.dict(os.environ, {"JWT_SECRET_KEY": "   "}):
            with self.assertRaises(RuntimeError) as ctx:
                get_jwt_secret_key()
            self.assertIn("not configured", str(ctx.exception))

    def test_jwt_algorithm_default_and_override(self):
        """JWT algorithm defaults to HS256 and supports override."""
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(get_jwt_algorithm(), "HS256")

        with patch.dict(os.environ, {"JWT_ALGORITHM": "HS384"}):
            self.assertEqual(get_jwt_algorithm(), "HS384")

    # -------------------------------------------------------------------------
    # 4. CWD-Independent Environment Loading Tests
    # -------------------------------------------------------------------------

    def test_backend_dir_resolution(self):
        """BACKEND_DIR in database module resolves to actual backend directory."""
        self.assertTrue(hasattr(db_module, "BACKEND_DIR"))
        backend_dir = db_module.BACKEND_DIR
        self.assertTrue(backend_dir.is_dir())
        self.assertTrue((backend_dir / "app").is_dir())
        self.assertTrue((backend_dir / "app" / "database.py").is_file())

    def test_normalize_database_url_postgresql(self):
        """Standard postgresql:// and postgres:// URLs are normalized to postgresql+psycopg://."""
        from app.database import normalize_database_url
        self.assertEqual(
            normalize_database_url("postgresql://user:pass@host:5432/db"),
            "postgresql+psycopg://user:pass@host:5432/db",
        )
        self.assertEqual(
            normalize_database_url("postgres://user:pass@host:5432/db"),
            "postgresql+psycopg://user:pass@host:5432/db",
        )
        self.assertEqual(
            normalize_database_url("postgresql+psycopg://user:pass@host:5432/db"),
            "postgresql+psycopg://user:pass@host:5432/db",
        )
        self.assertEqual(
            normalize_database_url("sqlite:///./test.db"),
            "sqlite:///./test.db",
        )


if __name__ == "__main__":
    unittest.main()
