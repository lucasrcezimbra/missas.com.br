from http import HTTPStatus

import pytest
from django.shortcuts import resolve_url
from model_bakery import baker
from pytest_django.asserts import (
    assertContains,
    assertInHTML,
    assertNotContains,
    assertTemplateUsed,
)

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
    assertContains(response, f"/{state.slug}/{city_with_parish_with_schedule.slug}/")
    assertContains(response, city_with_parish_with_schedule.name)


@pytest.mark.django_db
def test_order_by_cities_with_schedules_and_by_name(client):
    state = baker.make(State)

    cityA_with_schedule = baker.make(
        City, state=state, name="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    )
    cityB_with_schedule = baker.make(
        City, state=state, name="BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB"
    )
    cityA_without_schedule = baker.make(
        City, state=state, name="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    )
    cityB_without_schedule = baker.make(
        City, state=state, name="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    )

    baker.make(Schedule, parish__city=cityA_with_schedule)
    baker.make(Schedule, parish__city=cityB_with_schedule)

    response = client.get(resolve_url("cities_by_state", state=state.slug))

    html = response.content.decode()
    cityA_with_schedule_index = html.index(cityA_with_schedule.name)
    cityB_with_schedule_index = html.index(cityB_with_schedule.name)
    cityA_without_schedule_index = html.index(cityA_without_schedule.name)
    cityB_without_schedule_index = html.index(cityB_without_schedule.name)

    assert (
        cityA_with_schedule_index
        < cityB_with_schedule_index
        < cityA_without_schedule_index
        < cityB_without_schedule_index
    )


@pytest.mark.django_db
def test_title(client):
    state = baker.make(State)

    response = client.get(resolve_url("cities_by_state", state=state.slug))

    assertInHTML(
        f"<title>Horários de missas e confissões no {state.name}</title>",
        response.content.decode(),
    )
