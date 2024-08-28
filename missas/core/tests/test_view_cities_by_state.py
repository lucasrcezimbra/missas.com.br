from http import HTTPStatus

import pytest
from django.shortcuts import resolve_url
from model_bakery import baker
from pytest_django.asserts import assertContains, assertNotContains, assertTemplateUsed

from missas.core.models import City, State


@pytest.mark.django_db
def test_view_cities_by_state(client):
    state = baker.make(State)

    response = client.get(resolve_url("cities_by_state", state=state.slug))

    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_404_if_state_doesnt_exist(client):
    response = client.get(resolve_url("cities_by_state", state="unexist"))

    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_cache(client):
    state = baker.make(State)

    response = client.get(resolve_url("cities_by_state", state=state.slug))

    assert response.headers["Cache-Control"] == "max-age=86400"


@pytest.mark.django_db
def test_template(client):
    state = baker.make(State)

    response = client.get(resolve_url("cities_by_state", state=state.slug))

    assertTemplateUsed(response, "cities_by_state.html")


@pytest.mark.django_db
def test_all_cities(client):
    state = baker.make(State)
    cities = baker.make(City, state=state, _quantity=3)
    city_another_state = baker.make(City)

    response = client.get(resolve_url("cities_by_state", state=state.slug))

    assertContains(response, state.name)
    assertNotContains(response, city_another_state.name)
    for city in cities:
        assertContains(response, city.name)
