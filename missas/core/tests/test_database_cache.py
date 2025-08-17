import pytest
from django.core.cache import cache
from django.db import connection


@pytest.mark.django_db
def test_database_cache_functionality():
    """Test that the database cache backend is working correctly"""
    # Clear cache to start fresh
    cache.clear()

    # Test basic cache set and get
    key = "test_key"
    value = "test_value"

    cache.set(key, value, timeout=60)
    retrieved_value = cache.get(key)

    assert retrieved_value == value

    # Test that cache data is actually stored in database
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM missas_cache_table")
        count = cursor.fetchone()[0]
        assert count > 0, "Cache data should be stored in database table"

    # Test cache deletion
    cache.delete(key)
    assert cache.get(key) is None


@pytest.mark.django_db
def test_cache_table_exists():
    """Test that the cache table was created properly"""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_name='missas_cache_table'"
        )
        result = cursor.fetchone()
        assert result is not None, "Cache table 'missas_cache_table' should exist"
        assert result[0] == "missas_cache_table"


@pytest.mark.django_db
def test_cache_persistence_across_cache_operations():
    """Test that cache persists data and can handle multiple operations"""
    cache.clear()

    # Set multiple cache entries
    test_data = {
        "key1": "value1",
        "key2": {"nested": "dict"},
        "key3": [1, 2, 3, 4],
    }

    for key, value in test_data.items():
        cache.set(key, value, timeout=60)

    # Verify all entries can be retrieved
    for key, expected_value in test_data.items():
        retrieved_value = cache.get(key)
        assert retrieved_value == expected_value

    # Test cache.get_many
    retrieved_many = cache.get_many(test_data.keys())
    assert retrieved_many == test_data

    # Clean up
    cache.clear()
