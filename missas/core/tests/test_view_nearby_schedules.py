from datetime import time
from http import HTTPStatus

import pytest
from django.shortcuts import resolve_url
from model_bakery import baker
from pytest_django.asserts import assertContains, assertNotContains, assertTemplateUsed

from missas.core.models import Location, Schedule


@pytest.mark.django_db
def test_nearby_schedules_without_coordinates(client):
    response = client.get(resolve_url("nearby_schedules"))

    assert response.status_code == HTTPStatus.OK
    assertContains(response, "Coordenadas inválidas")


@pytest.mark.django_db
def test_nearby_schedules_with_invalid_coordinates(client):
    response = client.get(
        resolve_url("nearby_schedules"), {"lat": "invalid", "long": "invalid"}
    )

    assert response.status_code == HTTPStatus.OK
    assertContains(response, "Coordenadas inválidas")


@pytest.mark.django_db
def test_nearby_schedules_basic(client):
    location = baker.make(Location, latitude=-5.7945, longitude=-35.2110)
    schedule = baker.make(Schedule, location=location)

    response = client.get(
        resolve_url("nearby_schedules"), {"lat": "-5.7945", "long": "-35.2110"}
    )

    assert response.status_code == HTTPStatus.OK
    assertContains(response, schedule.parish.name)


@pytest.mark.django_db
def test_nearby_schedules_filters_by_distance(client):
    location_near = baker.make(Location, latitude=-5.7945, longitude=-35.2110)
    location_far = baker.make(Location, latitude=-15.7945, longitude=-47.8825)
    schedule_near = baker.make(Schedule, location=location_near)
    schedule_far = baker.make(Schedule, location=location_far)

    response = client.get(
        resolve_url("nearby_schedules"),
        {"lat": "-5.7945", "long": "-35.2110", "distancia": "10"},
    )

    assertContains(response, schedule_near.parish.name)
    assertNotContains(response, schedule_far.parish.name)


@pytest.mark.django_db
def test_nearby_schedules_shows_distance(client):
    location = baker.make(Location, latitude=-5.7945, longitude=-35.2110)
    baker.make(Schedule, location=location)

    response = client.get(
        resolve_url("nearby_schedules"), {"lat": "-5.7945", "long": "-35.2110"}
    )

    assertContains(response, "km")


@pytest.mark.django_db
def test_nearby_schedules_excludes_schedules_without_location(client):
    location = baker.make(Location, latitude=-5.7945, longitude=-35.2110)
    schedule_with_location = baker.make(Schedule, location=location)
    schedule_without_location = baker.make(Schedule, location=None)

    response = client.get(
        resolve_url("nearby_schedules"), {"lat": "-5.7945", "long": "-35.2110"}
    )

    assertContains(response, schedule_with_location.parish.name)
    assertNotContains(response, schedule_without_location.parish.name)


@pytest.mark.django_db
def test_nearby_schedules_excludes_schedules_without_coordinates(client):
    location_with_coords = baker.make(Location, latitude=-5.7945, longitude=-35.2110)
    location_without_coords = baker.make(Location, latitude=None, longitude=None)
    schedule_with_coords = baker.make(Schedule, location=location_with_coords)
    schedule_without_coords = baker.make(Schedule, location=location_without_coords)

    response = client.get(
        resolve_url("nearby_schedules"), {"lat": "-5.7945", "long": "-35.2110"}
    )

    assertContains(response, schedule_with_coords.parish.name)
    assertNotContains(response, schedule_without_coords.parish.name)


@pytest.mark.django_db
def test_nearby_schedules_filter_by_day(client):
    location = baker.make(Location, latitude=-5.7945, longitude=-35.2110)
    schedule_saturday = baker.make(
        Schedule, location=location, day=Schedule.Day.SATURDAY
    )
    schedule_sunday = baker.make(Schedule, location=location, day=Schedule.Day.SUNDAY)

    response = client.get(
        resolve_url("nearby_schedules"),
        {"lat": "-5.7945", "long": "-35.2110", "dia": "sabado"},
    )

    assertContains(response, schedule_saturday.parish.name)
    assertNotContains(response, schedule_sunday.parish.name)


@pytest.mark.django_db
def test_nearby_schedules_filter_by_time(client):
    location = baker.make(Location, latitude=-5.7945, longitude=-35.2110)
    schedule_morning = baker.make(Schedule, location=location, start_time=time(9, 0))
    schedule_afternoon = baker.make(Schedule, location=location, start_time=time(14, 0))

    response = client.get(
        resolve_url("nearby_schedules"),
        {"lat": "-5.7945", "long": "-35.2110", "horario": "12"},
    )

    assertContains(response, schedule_afternoon.parish.name)
    assertNotContains(response, schedule_morning.parish.name)


@pytest.mark.django_db
def test_nearby_schedules_filter_by_type(client):
    location = baker.make(Location, latitude=-5.7945, longitude=-35.2110)
    mass = baker.make(Schedule, location=location, type=Schedule.Type.MASS)
    confession = baker.make(Schedule, location=location, type=Schedule.Type.CONFESSION)

    response = client.get(
        resolve_url("nearby_schedules"),
        {"lat": "-5.7945", "long": "-35.2110", "tipo": "confissoes"},
    )

    assertContains(response, confession.parish.name)
    assertNotContains(response, mass.parish.name)


@pytest.mark.django_db
def test_nearby_schedules_filter_by_verified(client):
    location = baker.make(Location, latitude=-5.7945, longitude=-35.2110)
    verified = baker.make(Schedule, location=location, _fill_optional=["verified_at"])
    unverified = baker.make(Schedule, location=location)

    response = client.get(
        resolve_url("nearby_schedules"),
        {"lat": "-5.7945", "long": "-35.2110", "verificado": "1"},
    )

    assertContains(response, verified.parish.name)
    assertNotContains(response, unverified.parish.name)


@pytest.mark.django_db
def test_nearby_schedules_orders_by_distance(client):
    location_near = baker.make(Location, latitude=-5.7945, longitude=-35.2110)
    location_far = baker.make(Location, latitude=-5.8945, longitude=-35.3110)
    schedule_near = baker.make(
        Schedule,
        location=location_near,
        day=Schedule.Day.SUNDAY,
        start_time=time(10, 0),
    )
    schedule_far = baker.make(
        Schedule, location=location_far, day=Schedule.Day.SUNDAY, start_time=time(10, 0)
    )

    response = client.get(
        resolve_url("nearby_schedules"),
        {"lat": "-5.7945", "long": "-35.2110", "distancia": "50"},
    )

    content = response.content.decode()
    near_pos = content.find(schedule_near.parish.name)
    far_pos = content.find(schedule_far.parish.name)

    assert near_pos < far_pos


@pytest.mark.django_db
def test_nearby_schedules_template(client):
    response = client.get(
        resolve_url("nearby_schedules"), {"lat": "-5.7945", "long": "-35.2110"}
    )

    assertTemplateUsed(response, "nearby_schedules.html")


@pytest.mark.parametrize(
    ("hx_request", "hx_boosted", "expected_template"),
    (
        (True, True, "nearby_schedules.html"),
        (True, False, "cards.html"),
        (False, True, "nearby_schedules.html"),
        (False, False, "nearby_schedules.html"),
    ),
)
@pytest.mark.django_db
def test_nearby_schedules_htmx_template(
    client, hx_request, hx_boosted, expected_template
):
    response = client.get(
        resolve_url("nearby_schedules"),
        {"lat": "-5.7945", "long": "-35.2110"},
        headers={"HX-Request": hx_request, "HX-Boosted": hx_boosted},
    )

    assertTemplateUsed(response, expected_template)


@pytest.mark.django_db
def test_nearby_schedules_preserves_coordinates_in_form(client):
    response = client.get(
        resolve_url("nearby_schedules"), {"lat": "-5.7945", "long": "-35.2110"}
    )

    assertContains(response, 'name="lat"')
    assertContains(response, 'name="long"')
