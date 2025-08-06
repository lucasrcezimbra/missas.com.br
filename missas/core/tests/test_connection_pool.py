"""Tests for database connection pooling configuration."""

import pytest
from django.conf import settings
from django.db import connection


class TestConnectionPool:
    """Test database connection pooling configuration."""

    def test_pool_option_is_configured(self):
        """Test that the pool option is configured in database settings."""
        db_config = settings.DATABASES["default"]

        assert "OPTIONS" in db_config
        assert "pool" in db_config["OPTIONS"]
        assert db_config["OPTIONS"]["pool"] is True

    @pytest.mark.django_db
    def test_connection_can_be_established(self):
        """Test that database connection can be established with pooling enabled."""
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result == (1,)

    def test_psycopg_pool_is_available(self):
        """Test that psycopg_pool module is available."""
        try:
            import psycopg_pool

            assert hasattr(psycopg_pool, "ConnectionPool")
        except ImportError:
            pytest.fail("psycopg_pool should be available for connection pooling")
