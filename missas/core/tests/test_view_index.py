from http import HTTPStatus

import pytest
from django.shortcuts import resolve_url

from missas.core.models import City, State


def test_home_page_renders(client):
    response = client.get(resolve_url("index"))

    assert response.status_code == HTTPStatus.OK
    assert "Sobre o Projeto" in response.content.decode()


@pytest.mark.django_db
def test_home_page_shows_states_and_cities(client):
    # Create test data
    state = State.objects.create(name="Test State", short_name="TS", slug="test-state")
    city = City.objects.create(name="Test City", slug="test-city", state=state)

    response = client.get(resolve_url("index"))

    assert response.status_code == HTTPStatus.OK
    content = response.content.decode()
    assert "Test State" in content
    assert "Test City" in content
