from datetime import time
from http import HTTPStatus

import pytest
from django.shortcuts import resolve_url
from django.test.client import Client
from model_bakery import baker
from pytest_django.asserts import (
    assertContains,
    assertInHTML,
    assertNotContains,
    assertQuerySetEqual,
    assertTemplateUsed,
)

from missas.core.models import Parish, Schedule, Source


@pytest.mark.django_db
def test_404_if_parish_doesnt_exist(client):
    response = client.get(resolve_url("by_parish", parish="unknown"))
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_view_by_parish(client):
    parish = baker.make(Parish)

    response = client.get(resolve_url("by_parish", parish=parish.slug))

    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    ("hx_request", "hx_boosted", "expected_template"),
    (
        (True, True, "parish_schedules.html"),
        (True, False, "cards.html"),
        (False, True, "parish_schedules.html"),
        (False, False, "parish_schedules.html"),
    ),
)
@pytest.mark.django_db
def test_template(client, hx_request, hx_boosted, expected_template):
    parish = baker.make(Parish)

    response = client.get(
        resolve_url("by_parish", parish=parish.slug),
        headers={"HX-Request": hx_request, "HX-Boosted": hx_boosted},
    )

    assertTemplateUsed(response, expected_template)


@pytest.mark.django_db
def test_show_schedules_by_parish(client: Client):
    parish = baker.make(Parish)
    another_parish = baker.make(Parish)
    schedule = baker.make(Schedule, start_time=time(9, 57), parish=parish)
    another_schedule = baker.make(
        Schedule, start_time=time(8, 12), parish=another_parish
    )

    response = client.get(
        resolve_url("by_parish", parish=parish.slug),
    )

    assertContains(response, schedule.get_day_display())
    assertContains(response, "9:57")
    assertContains(response, schedule.parish.name)

    assertNotContains(response, "8:12")
    assertNotContains(response, another_schedule.parish.name)


@pytest.mark.django_db
def test_filter_by_day(client: Client):
    parish = baker.make(Parish)
    schedule = baker.make(Schedule, parish=parish, day=Schedule.Day.SATURDAY)
    another_schedule = baker.make(Schedule, parish=parish, day=Schedule.Day.SUNDAY)

    response = client.get(
        resolve_url("by_parish", parish=parish.slug),
        data={"dia": "sabado"},
    )

    assertContains(response, schedule.parish.name)
    assertNotContains(response, another_schedule.parish.name)


@pytest.mark.django_db
def test_filter_by_sunday(client: Client):
    parish = baker.make(Parish)
    sunday = baker.make(Schedule, parish=parish, day=Schedule.Day.SUNDAY)
    saturday = baker.make(Schedule, parish=parish, day=Schedule.Day.SATURDAY)

    response = client.get(
        resolve_url("by_parish", parish=parish.slug),
        data={"dia": "domingo"},
    )

    assertContains(response, sunday.parish.name)
    assertNotContains(response, saturday.parish.name)


@pytest.mark.django_db
def test_order_by_day_and_time(client: Client):
    parish = baker.make(Parish)
    saturday_morning = baker.make(
        Schedule, day=Schedule.Day.SATURDAY, start_time=time(9, 57), parish=parish
    )
    saturday_afternoon = baker.make(
        Schedule, day=Schedule.Day.SATURDAY, start_time=time(14, 12), parish=parish
    )
    sunday_morning = baker.make(
        Schedule, day=Schedule.Day.SUNDAY, start_time=time(9, 57), parish=parish
    )
    sunday_afternoon = baker.make(
        Schedule, day=Schedule.Day.SUNDAY, start_time=time(14, 12), parish=parish
    )

    response = client.get(
        resolve_url("by_parish", parish=parish.slug),
    )

    assertQuerySetEqual(
        response.context["schedules"],
        [
            sunday_morning,
            sunday_afternoon,
            saturday_morning,
            saturday_afternoon,
        ],
    )


@pytest.mark.django_db
def test_filter_by_day_and_order_by_time(client: Client):
    parish = baker.make(Parish)
    saturday_morning = baker.make(
        Schedule, day=Schedule.Day.SATURDAY, start_time=time(9, 57), parish=parish
    )
    saturday_afternoon = baker.make(
        Schedule, day=Schedule.Day.SATURDAY, start_time=time(14, 12), parish=parish
    )
    baker.make(Schedule, day=Schedule.Day.SUNDAY, start_time=time(9, 57), parish=parish)
    baker.make(
        Schedule, day=Schedule.Day.SUNDAY, start_time=time(14, 12), parish=parish
    )

    response = client.get(
        resolve_url("by_parish", parish=parish.slug),
        data={"dia": "sabado"},
    )

    assertQuerySetEqual(
        response.context["schedules"],
        [
            saturday_morning,
            saturday_afternoon,
        ],
    )


@pytest.mark.django_db
def test_no_schedules(client: Client):
    parish = baker.make(Parish)

    response = client.get(
        resolve_url("by_parish", parish=parish.slug),
    )

    assertContains(response, "Nenhum horário cadastrado.")


@pytest.mark.django_db
def test_filter_by_time(client: Client):
    parish = baker.make(Parish)
    baker.make(Schedule, day=Schedule.Day.SUNDAY, start_time=time(9, 57), parish=parish)
    sunday_afternoon = baker.make(
        Schedule, day=Schedule.Day.SUNDAY, start_time=time(14, 12), parish=parish
    )

    response = client.get(
        resolve_url("by_parish", parish=parish.slug),
        data={"horario": "12"},
    )

    assertQuerySetEqual(
        response.context["schedules"],
        [sunday_afternoon],
    )


@pytest.mark.django_db
def test_filter_by_type_default_mass(client):
    parish = baker.make(Parish)
    mass = baker.make(Schedule, parish=parish, type=Schedule.Type.MASS)
    baker.make(Schedule, parish=parish, type=Schedule.Type.CONFESSION)

    response = client.get(
        resolve_url("by_parish", parish=parish.slug),
    )
    assertQuerySetEqual(
        response.context["schedules"],
        [mass],
    )
    assertInHTML(
        '<input class="btn-check" id="missas" name="tipo" type="radio" value="missas" checked>',
        response.content.decode(),
    )


@pytest.mark.django_db
def test_filter_by_type(client):
    parish = baker.make(Parish)
    baker.make(Schedule, parish=parish, type=Schedule.Type.MASS)
    confession = baker.make(Schedule, parish=parish, type=Schedule.Type.CONFESSION)

    response = client.get(
        resolve_url("by_parish", parish=parish.slug),
        data={"tipo": "confissoes"},
    )

    assertInHTML(
        '<input class="btn-check" id="confissoes" name="tipo" type="radio" value="confissoes" checked>',
        response.content.decode(),
    )
    assertQuerySetEqual(
        response.context["schedules"],
        [confession],
    )


@pytest.mark.django_db
def test_show_end_time(client: Client):
    parish = baker.make(Parish)
    baker.make(
        Schedule,
        type=Schedule.Type.CONFESSION,
        start_time=time(9),
        end_time=time(11),
        parish=parish,
    )

    response = client.get(
        resolve_url("by_parish", parish=parish.slug),
        data={"tipo": "confissoes"},
    )

    assertContains(response, "9:00")
    assertContains(response, "11:00")


@pytest.mark.django_db
def test_filter_by_end_time_if_exists(client: Client):
    parish = baker.make(Parish)
    confession = baker.make(
        Schedule,
        type=Schedule.Type.CONFESSION,
        start_time=time(9),
        end_time=time(11),
        parish=parish,
    )

    response = client.get(
        resolve_url("by_parish", parish=parish.slug),
        data={"tipo": "confissoes", "horario": "10"},
    )

    assertQuerySetEqual(response.context["schedules"], [confession])


@pytest.mark.django_db
def test_filter_by_verified(client: Client):
    parish = baker.make(Parish)
    verified = baker.make(Schedule, parish=parish, _fill_optional=["verified_at"])
    unverified = baker.make(Schedule, parish=parish)

    response = client.get(
        resolve_url("by_parish", parish=parish.slug),
        data={"verificado": "1"},
    )

    assertContains(response, verified.parish.name)
    assertNotContains(response, unverified.parish.name)


@pytest.mark.parametrize(
    ["weekday"],
    (
        ["segunda"],
        ["terca"],
        ["quarta"],
        ["quinta"],
        ["sexta"],
        ["sabado"],
        ["domingo"],
    ),
)
@pytest.mark.django_db
def test_checked_day(client, weekday):
    parish = baker.make(Parish)

    response = client.get(
        resolve_url("by_parish", parish=parish.slug),
        data={"dia": weekday},
    )

    assertInHTML(
        f'<input class="btn-check" id="{weekday}" name="dia" type="radio" value="{weekday}" checked>',
        response.content.decode(),
    )


@pytest.mark.django_db
def test_schedule_with_source(client):
    source = baker.make(Source)
    schedule = baker.make(Schedule, source=source)

    parish = schedule.parish
    response = client.get(resolve_url("by_parish", parish=parish.slug))

    html = response.content.decode()
    assert source.description in html


@pytest.mark.django_db
def test_schedule_with_source_with_link(client):
    source = baker.make(Source, _fill_optional=["link"])
    schedule = baker.make(Schedule, source=source)

    parish = schedule.parish
    response = client.get(resolve_url("by_parish", parish=parish.slug))

    html = response.content.decode()
    assert f'href="{source.link}"' in html


@pytest.mark.django_db
def test_verified_schedule(client):
    schedule = baker.make(Schedule, _fill_optional=["verified_at"])

    parish = schedule.parish
    response = client.get(resolve_url("by_parish", parish=parish.slug))

    html = response.content.decode()
    assert f"Verificado por Missas.com.br em {schedule.verified_at:%d/%m/%Y}" in html


@pytest.mark.django_db
def test_schedule_with_location(client):
    schedule = baker.make(Schedule, _fill_optional=["location"])

    parish = schedule.parish
    response = client.get(resolve_url("by_parish", parish=parish.slug))

    html = response.content.decode()
    assert schedule.location in html


@pytest.mark.django_db
def test_breadcrumb_to_state(client):
    schedule = baker.make(Schedule)

    parish = schedule.parish
    response = client.get(resolve_url("by_parish", parish=parish.slug))

    html = response.content.decode()
    assert f'<a href="/{parish.city.state.slug}">{parish.city.state.name}</a>' in html


@pytest.mark.django_db
def test_number_of_queries(client, django_assert_max_num_queries):
    parish = baker.make(Parish)
    baker.make(Schedule, parish=parish, _quantity=100)

    with django_assert_max_num_queries(5):
        response = client.get(resolve_url("by_parish", parish=parish.slug))

    assert response.status_code == HTTPStatus.OK
