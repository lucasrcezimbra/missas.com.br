from http import HTTPStatus

import pytest
from django.shortcuts import resolve_url
from model_bakery import baker
from pytest_django.asserts import assertContains, assertNotContains, assertTemplateUsed

from missas.core.models import City, Parish, Schedule, State


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


@pytest.mark.django_db
def test_only_cities_with_parishes_and_schedules_have_link(client):
    state = baker.make(State)

    city_with_parish_with_schedule = baker.make(City, state=state)
    city_with_parish_without_schedule = baker.make(City, state=state)
    city_without_parish = baker.make(City, state=state)

    parish_with_schedule = baker.make(Parish, city=city_with_parish_with_schedule)
    baker.make(Parish, city=city_with_parish_without_schedule)

    baker.make(Schedule, parish=parish_with_schedule)

    response = client.get(resolve_url("cities_by_state", state=state.slug))

    assertNotContains(response, f"/{city_without_parish.slug}")
    assertNotContains(response, f"/{city_with_parish_without_schedule.slug}")
    assertContains(
        response,
        f'<a href="/{state.slug}/{city_with_parish_with_schedule.slug}/">{city_with_parish_with_schedule.name}</a>',
        html=True,
    )
