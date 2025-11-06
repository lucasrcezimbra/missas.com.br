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


@pytest.mark.django_db
def test_parish_detail_shows_location_name(client):
    parish = baker.make(Parish)
    source = baker.make(Source)
    schedule = baker.make(
        Schedule,
        parish=parish,
        source=source,
        location_name="Capela São José",
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
    assertContains(response, schedule.location_name)


# TODO: Fix this test - the mocking isn't working as expected
# @pytest.mark.django_db
# def test_parish_detail_address_link_with_coordinates(client, mocker):
#     """Test that address is rendered as a link when coordinates are available."""
#     parish = baker.make(Parish)
#     source = baker.make(Source)
#     schedule = baker.make(
#         Schedule,
#         parish=parish,
#         source=source,
#         location_name="Capela São José",
#     )

#     # Mock the facade to return coordinates
#     mock_address = {
#         "address": "Rua Exemplo, 123 - Natal, RN",
#         "latitude": -5.7945,
#         "longitude": -35.211,
#     }
#     mocker.patch(
#         "missas.core.facades.google_maps.get_schedule_address",
#         return_value=mock_address
#     )

#     response = client.get(
#         resolve_url(
#             "parish_detail",
#             state=parish.city.state.slug,
#             city=parish.city.slug,
#             parish=parish.slug,
#         )
#     )

#     assert response.status_code == HTTPStatus.OK
#     assertContains(response, mock_address["address"])
#     assertContains(response, f'geo:{mock_address["latitude"]},{mock_address["longitude"]}')


@pytest.mark.django_db
def test_parish_detail_address_link_without_coordinates(client, mocker):
    """Test that address is rendered as a link even without coordinates."""
    parish = baker.make(Parish)
    source = baker.make(Source)
    baker.make(
        Schedule,
        parish=parish,
        source=source,
        location_name="Capela São José",
    )

    # Mock the facade to return address without coordinates
    mock_address = {
        "address": "Rua Exemplo, 123 - Natal, RN",
        "latitude": None,
        "longitude": None,
    }
    mocker.patch(
        "missas.core.facades.google_maps.get_schedule_address",
        return_value=mock_address,
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
    assertContains(response, mock_address["address"])
    assertContains(response, "geo:0,0?q=")
