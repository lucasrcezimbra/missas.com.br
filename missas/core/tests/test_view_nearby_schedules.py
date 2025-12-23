from datetime import time
from http import HTTPStatus

import pytest
from django.shortcuts import resolve_url
from model_bakery import baker
from pytest_django.asserts import assertContains, assertNotContains

from missas.core.models import Location, Schedule


@pytest.mark.django_db
def test_nearby_schedules_requires_lat_and_long(client):
    response = client.get(resolve_url("nearby_schedules"))

    assert response.status_code == HTTPStatus.OK
    assertContains(response, "Coordenadas inválidas")


@pytest.mark.django_db
def test_nearby_schedules_with_invalid_coordinates(client):
    response = client.post(
        resolve_url("nearby_schedules"), data={"lat": "invalid", "long": "invalid"}
    )

    assert response.status_code == HTTPStatus.OK
    assertContains(response, "Coordenadas inválidas")


@pytest.mark.django_db
def test_nearby_schedules_shows_schedules_with_location(client):
    location = baker.make(Location, latitude=-5.795399, longitude=-35.211336)
    schedule = baker.make(Schedule, location=location, start_time=time(9, 0))

    response = client.post(
        resolve_url("nearby_schedules"), data={"lat": -5.795399, "long": -35.211336}
    )

    assert response.status_code == HTTPStatus.OK
    assertContains(response, schedule.parish.name)
    assertContains(response, "9:00")


@pytest.mark.django_db
def test_nearby_schedules_filters_by_max_distance(client):
    location_close = baker.make(Location, latitude=-5.795399, longitude=-35.211336)
    location_far = baker.make(Location, latitude=-5.895399, longitude=-35.311336)
    close_schedule = baker.make(Schedule, location=location_close)
    far_schedule = baker.make(Schedule, location=location_far)

    # POST to set coordinates
    client.post(
        resolve_url("nearby_schedules"), data={"lat": -5.795399, "long": -35.211336}
    )
    # Then GET with distance filter
    response = client.get(resolve_url("nearby_schedules") + "?distancia=5")

    assertContains(response, close_schedule.parish.name)
    assertNotContains(response, far_schedule.parish.name)


@pytest.mark.django_db
def test_nearby_schedules_orders_by_distance(client):
    location1 = baker.make(Location, latitude=-5.795399, longitude=-35.211336)
    location2 = baker.make(Location, latitude=-5.805399, longitude=-35.221336)
    location3 = baker.make(Location, latitude=-5.815399, longitude=-35.231336)
    schedule1 = baker.make(Schedule, location=location1)
    schedule2 = baker.make(Schedule, location=location2)
    schedule3 = baker.make(Schedule, location=location3)

    response = client.post(
        resolve_url("nearby_schedules"),
        data={"lat": -5.795399, "long": -35.211336},
        follow=True,
    )

    schedules = response.context["schedules"]
    assert schedules[0].parish.id == schedule1.parish.id
    assert schedules[1].parish.id == schedule2.parish.id
    assert schedules[2].parish.id == schedule3.parish.id


@pytest.mark.django_db
def test_nearby_schedules_shows_distance(client):
    location = baker.make(Location, latitude=-5.795399, longitude=-35.211336)
    baker.make(Schedule, location=location)

    response = client.post(
        resolve_url("nearby_schedules"), data={"lat": -5.795399, "long": -35.211336}
    )

    assertContains(response, "km")


@pytest.mark.django_db
def test_nearby_schedules_filters_by_day(client):
    location1 = baker.make(Location, latitude=-5.795399, longitude=-35.211336)
    location2 = baker.make(Location, latitude=-5.795399, longitude=-35.211336)
    sunday_schedule = baker.make(Schedule, location=location1, day=Schedule.Day.SUNDAY)
    monday_schedule = baker.make(Schedule, location=location2, day=Schedule.Day.MONDAY)

    # POST to set coordinates
    client.post(
        resolve_url("nearby_schedules"), data={"lat": -5.795399, "long": -35.211336}
    )
    # Then GET with day filter
    response = client.get(resolve_url("nearby_schedules") + "?dia=domingo")

    assertContains(response, sunday_schedule.parish.name)
    assertNotContains(response, monday_schedule.parish.name)


@pytest.mark.django_db
def test_nearby_schedules_filters_by_type(client):
    location1 = baker.make(Location, latitude=-5.795399, longitude=-35.211336)
    location2 = baker.make(Location, latitude=-5.795399, longitude=-35.211336)
    mass = baker.make(Schedule, location=location1, type=Schedule.Type.MASS)
    confession = baker.make(Schedule, location=location2, type=Schedule.Type.CONFESSION)

    # POST to set coordinates
    client.post(
        resolve_url("nearby_schedules"), data={"lat": -5.795399, "long": -35.211336}
    )
    # Then GET with type filter
    response = client.get(resolve_url("nearby_schedules") + "?tipo=confissoes")

    assertContains(response, confession.parish.name)
    assertNotContains(response, mass.parish.name)


@pytest.mark.django_db
def test_nearby_schedules_filters_by_verified(client):
    location1 = baker.make(Location, latitude=-5.795399, longitude=-35.211336)
    location2 = baker.make(Location, latitude=-5.795399, longitude=-35.211336)
    verified = baker.make(Schedule, location=location1, _fill_optional=["verified_at"])
    unverified = baker.make(Schedule, location=location2)

    # POST to set coordinates
    client.post(
        resolve_url("nearby_schedules"), data={"lat": -5.795399, "long": -35.211336}
    )
    # Then GET with verified filter
    response = client.get(resolve_url("nearby_schedules") + "?verificado=1")

    assertContains(response, verified.parish.name)
    assertNotContains(response, unverified.parish.name)


@pytest.mark.django_db
def test_nearby_schedules_filters_by_time(client):
    location1 = baker.make(Location, latitude=-5.795399, longitude=-35.211336)
    location2 = baker.make(Location, latitude=-5.795399, longitude=-35.211336)
    morning = baker.make(Schedule, location=location1, start_time=time(9, 0))
    afternoon = baker.make(Schedule, location=location2, start_time=time(14, 0))

    # POST to set coordinates
    client.post(
        resolve_url("nearby_schedules"), data={"lat": -5.795399, "long": -35.211336}
    )
    # Then GET with time filter
    response = client.get(resolve_url("nearby_schedules") + "?horario=12")

    assertContains(response, afternoon.parish.name)
    assertNotContains(response, morning.parish.name)


@pytest.mark.django_db
def test_nearby_schedules_excludes_schedules_without_location(client):
    location = baker.make(Location, latitude=-5.795399, longitude=-35.211336)
    with_location = baker.make(Schedule, location=location)
    without_location = baker.make(Schedule, location=None)

    response = client.post(
        resolve_url("nearby_schedules"), data={"lat": -5.795399, "long": -35.211336}
    )

    assertContains(response, with_location.parish.name)
    assertNotContains(response, without_location.parish.name)


@pytest.mark.django_db
def test_nearby_schedules_no_schedules(client):
    response = client.post(
        resolve_url("nearby_schedules"), data={"lat": -5.795399, "long": -35.211336}
    )

    assertContains(response, "Nenhum horário cadastrado próximo à sua localização.")
