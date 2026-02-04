from http import HTTPStatus

import pytest
from django.shortcuts import resolve_url
from model_bakery import baker
from pytest_django.asserts import assertContains, assertTemplateUsed

from missas.core.models import Location, Parish, Schedule, Source


@pytest.mark.django_db
def test_status_code_and_template(client):
    location = baker.make(Location)
    parish = baker.make(Parish)
    baker.make(Schedule, location=location, parish=parish)

    response = client.get(resolve_url("location_detail", pk=location.pk))

    assert response.status_code == HTTPStatus.OK
    assertTemplateUsed(response, "location_detail.html")


@pytest.mark.django_db
def test_page_title(client):
    location = baker.make(Location, name="Capela do Hospital")
    parish = baker.make(Parish)
    baker.make(Schedule, location=location, parish=parish)

    response = client.get(resolve_url("location_detail", pk=location.pk))

    assertContains(response, "Capela do Hospital")


@pytest.mark.django_db
def test_shows_location_address(client):
    location = baker.make(Location, address="Rua das Flores, 123")
    parish = baker.make(Parish)
    baker.make(Schedule, location=location, parish=parish)

    response = client.get(resolve_url("location_detail", pk=location.pk))

    assertContains(response, "Rua das Flores, 123")
    assertContains(response, "google.com/maps/search")


@pytest.mark.django_db
def test_shows_parish_link(client):
    location = baker.make(Location)
    parish = baker.make(Parish, name="Paróquia São João")
    baker.make(Schedule, location=location, parish=parish)

    response = client.get(resolve_url("location_detail", pk=location.pk))

    assertContains(response, "Parte de")
    assertContains(response, "Paróquia São João")
    assertContains(
        response,
        resolve_url(
            "parish_detail",
            state=parish.city.state.slug,
            city=parish.city.slug,
            parish=parish.slug,
        ),
    )


@pytest.mark.django_db
def test_shows_schedules(client):
    location = baker.make(Location)
    parish = baker.make(Parish)
    source = baker.make(Source)
    schedule = baker.make(
        Schedule,
        location=location,
        parish=parish,
        source=source,
        type=Schedule.Type.MASS,
        day=Schedule.Day.SUNDAY,
    )

    response = client.get(resolve_url("location_detail", pk=location.pk))

    assertContains(response, "Horários de Missas e Confissões")
    assertContains(response, "Missas")
    assertContains(response, schedule.get_day_display())


@pytest.mark.django_db
def test_shows_confessions(client):
    location = baker.make(Location)
    parish = baker.make(Parish)
    source = baker.make(Source)
    baker.make(
        Schedule,
        location=location,
        parish=parish,
        source=source,
        type=Schedule.Type.CONFESSION,
        day=Schedule.Day.SATURDAY,
    )

    response = client.get(resolve_url("location_detail", pk=location.pk))

    assertContains(response, "Confissões")


@pytest.mark.django_db
def test_returns_404_when_location_not_found(client):
    response = client.get(resolve_url("location_detail", pk=99999))

    assert response.status_code == HTTPStatus.NOT_FOUND
