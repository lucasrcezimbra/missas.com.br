from http import HTTPStatus

import pytest
from django.shortcuts import resolve_url
from model_bakery import baker
from pytest_django.asserts import assertContains, assertTemplateUsed

from missas.core.models import City, Parish, Schedule, Source, State


@pytest.mark.django_db
def test_404_if_state_doesnt_exist(client):
    response = client.get(
        resolve_url(
            "parish_detail", state="unknown", city="natal", parish="some-parish"
        )
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_404_if_city_doesnt_exist(client):
    state = baker.make(State)

    response = client.get(
        resolve_url(
            "parish_detail", state=state.slug, city="unknown", parish="some-parish"
        )
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_404_if_parish_doesnt_exist(client):
    city = baker.make(City)

    response = client.get(
        resolve_url(
            "parish_detail", state=city.state.slug, city=city.slug, parish="unknown"
        )
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_parish_detail_view_renders_correctly(client):
    parish = baker.make(Parish)

    response = client.get(
        resolve_url(
            "parish_detail",
            state=parish.city.state.slug,
            city=parish.city.slug,
            parish=parish.slug,
        )
    )

    assert response.status_code == HTTPStatus.OK
    assertTemplateUsed(response, "parish_detail.html")
    assertContains(response, parish.name)
    assertContains(response, parish.city.name)
    assertContains(response, parish.city.state.name)


@pytest.mark.django_db
def test_parish_detail_shows_contact_information(client):
    parish = baker.make(Parish)
    contact = baker.make(
        "core.Contact", parish=parish, email="test@example.com", phone="+5511999999999"
    )

    response = client.get(
        resolve_url(
            "parish_detail",
            state=parish.city.state.slug,
            city=parish.city.slug,
            parish=parish.slug,
        )
    )

    assert response.status_code == HTTPStatus.OK
    assertContains(response, "Informações de Contato")
    assertContains(response, contact.email)
    assertContains(response, contact.phone)


@pytest.mark.django_db
def test_parish_detail_shows_schedules(client):
    parish = baker.make(Parish)
    source = baker.make(Source)
    schedule = baker.make(
        Schedule,
        parish=parish,
        source=source,
        type=Schedule.Type.MASS,
        day=Schedule.Day.SUNDAY,
    )

    response = client.get(
        resolve_url(
            "parish_detail",
            state=parish.city.state.slug,
            city=parish.city.slug,
            parish=parish.slug,
        )
    )

    assert response.status_code == HTTPStatus.OK
    assertContains(response, "Horários de Missas e Confissões")
    assertContains(response, "Missas")
    assertContains(response, schedule.get_day_display())


@pytest.mark.django_db
def test_parish_detail_shows_confessions_separately(client):
    parish = baker.make(Parish)
    source = baker.make(Source)
    _mass_schedule = baker.make(
        Schedule,
        parish=parish,
        source=source,
        type=Schedule.Type.MASS,
        day=Schedule.Day.SUNDAY,
    )
    _confession_schedule = baker.make(
        Schedule,
        parish=parish,
        source=source,
        type=Schedule.Type.CONFESSION,
        day=Schedule.Day.SATURDAY,
    )

    response = client.get(
        resolve_url(
            "parish_detail",
            state=parish.city.state.slug,
            city=parish.city.slug,
            parish=parish.slug,
        )
    )

    assert response.status_code == HTTPStatus.OK
    assertContains(response, "Missas")
    assertContains(response, "Confissões")


@pytest.mark.django_db
def test_parish_detail_shows_no_schedules_message(client):
    parish = baker.make(Parish)

    response = client.get(
        resolve_url(
            "parish_detail",
            state=parish.city.state.slug,
            city=parish.city.slug,
            parish=parish.slug,
        )
    )

    assert response.status_code == HTTPStatus.OK
    assertContains(response, "Nenhum horário cadastrado")


@pytest.mark.django_db
def test_parish_detail_shows_verified_schedule(client):
    parish = baker.make(Parish)
    source = baker.make(Source)
    _schedule = baker.make(
        Schedule, parish=parish, source=source, verified_at="2023-01-01"
    )

    response = client.get(
        resolve_url(
            "parish_detail",
            state=parish.city.state.slug,
            city=parish.city.slug,
            parish=parish.slug,
        )
    )

    assert response.status_code == HTTPStatus.OK
    assertContains(response, "Verificado por Missas.com.br")
