from http import HTTPStatus

import pytest
from django.shortcuts import resolve_url


@pytest.mark.django_db
def test_index_renders_home_page(client):
    response = client.get(resolve_url("index"))

    assert response.status_code == HTTPStatus.OK
    assert "Bem-vindo ao Missas.com.br" in response.content.decode()
    assert "Nossos Números" in response.content.decode()
    assert "Estados e Cidades com Paróquias" in response.content.decode()
    assert "Projeto Open Source" in response.content.decode()


@pytest.mark.django_db
def test_index_contains_stats(client):
    response = client.get(resolve_url("index"))

    assert response.status_code == HTTPStatus.OK
    # Check that the template context contains the expected stats
    assert "stats" in response.context
    stats = response.context["stats"]
    assert "cities_with_parishes" in stats
    assert "parishes" in stats
    assert "schedules" in stats
    assert "verified_schedules" in stats


@pytest.mark.django_db
def test_index_contains_states_with_cities(client):
    response = client.get(resolve_url("index"))

    assert response.status_code == HTTPStatus.OK
    # Check that the template context contains states with cities
    assert "states_with_cities" in response.context
    states_with_cities = response.context["states_with_cities"]
    assert isinstance(states_with_cities, list)
