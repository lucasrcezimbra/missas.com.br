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

from missas.core.models import City, Schedule, Source, State


@pytest.mark.django_db
def test_404_if_state_doesnt_exist(client):
    response = client.get(resolve_url("by_city", state="unknown", city="natal"))
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_404_if_city_doesnt_exist(client):
    state = baker.make(State)

    response = client.get(resolve_url("by_city", state=state.slug, city="unknown"))

    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_view_by_city(client):
    city = baker.make(City)

    response = client.get(resolve_url("by_city", state=city.state.slug, city=city.slug))

    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_cache(client):
    city = baker.make(City)

    response = client.get(resolve_url("by_city", state=city.state.slug, city=city.slug))

    assert response.headers["Cache-Control"] == "max-age=86400"


@pytest.mark.parametrize(
    ("hx_request", "hx_boosted", "expected_template"),
    (
        (True, True, "parishes_by_city.html"),
        (True, False, "cards.html"),
        (False, True, "parishes_by_city.html"),
        (False, False, "parishes_by_city.html"),
    ),
)
@pytest.mark.django_db
def test_template(client, hx_request, hx_boosted, expected_template):
    city = baker.make(City)

    response = client.get(
        resolve_url("by_city", state=city.state.slug, city=city.slug),
        headers={"HX-Request": hx_request, "HX-Boosted": hx_boosted},
    )

    assertTemplateUsed(response, expected_template)


@pytest.mark.django_db
def test_show_schedules_by_city(client: Client):
    city = baker.make(City)
    another_city = baker.make(City)
    schedule = baker.make(Schedule, start_time=time(9, 57), parish__city=city)
    another_schedule = baker.make(
        Schedule, start_time=time(8, 12), parish__city=another_city
    )

    response = client.get(
        resolve_url("by_city", state=city.state.slug, city=city.slug),
    )

    assertContains(response, schedule.get_day_display())
    assertContains(response, "9:57")
    assertContains(response, schedule.parish.name)

    assertNotContains(response, "8:12")
    assertNotContains(response, another_schedule.parish.name)


@pytest.mark.django_db
def test_filter_by_day(client: Client):
    city = baker.make(City)
    schedule = baker.make(Schedule, parish__city=city, day=Schedule.Day.SATURDAY)
    another_schedule = baker.make(Schedule, parish__city=city, day=Schedule.Day.SUNDAY)

    response = client.get(
        resolve_url("by_city", state=city.state.slug, city=city.slug),
        data={"dia": "sabado"},
    )

    assertContains(response, schedule.parish.name)
    assertNotContains(response, another_schedule.parish.name)


@pytest.mark.django_db
def test_filter_by_sunday(client: Client):
    city = baker.make(City)
    sunday = baker.make(Schedule, parish__city=city, day=Schedule.Day.SUNDAY)
    saturday = baker.make(Schedule, parish__city=city, day=Schedule.Day.SATURDAY)

    response = client.get(
        resolve_url("by_city", state=city.state.slug, city=city.slug),
        data={"dia": "domingo"},
    )

    assertContains(response, sunday.parish.name)
    assertNotContains(response, saturday.parish.name)


@pytest.mark.django_db
def test_order_by_day_and_time(client: Client):
    city = baker.make(City)
    saturday_morning = baker.make(
        Schedule, day=Schedule.Day.SATURDAY, start_time=time(9, 57), parish__city=city
    )
    saturday_afternoon = baker.make(
        Schedule, day=Schedule.Day.SATURDAY, start_time=time(14, 12), parish__city=city
    )
    sunday_morning = baker.make(
        Schedule, day=Schedule.Day.SUNDAY, start_time=time(9, 57), parish__city=city
    )
    sunday_afternoon = baker.make(
        Schedule, day=Schedule.Day.SUNDAY, start_time=time(14, 12), parish__city=city
    )

    response = client.get(
        resolve_url("by_city", state=city.state.slug, city=city.slug),
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
    city = baker.make(City)
    saturday_morning = baker.make(
        Schedule, day=Schedule.Day.SATURDAY, start_time=time(9, 57), parish__city=city
    )
    saturday_afternoon = baker.make(
        Schedule, day=Schedule.Day.SATURDAY, start_time=time(14, 12), parish__city=city
    )
    baker.make(
        Schedule, day=Schedule.Day.SUNDAY, start_time=time(9, 57), parish__city=city
    )
    baker.make(
        Schedule, day=Schedule.Day.SUNDAY, start_time=time(14, 12), parish__city=city
    )

    response = client.get(
        resolve_url("by_city", state=city.state.slug, city=city.slug),
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
    city = baker.make(City)

    response = client.get(
        resolve_url("by_city", state=city.state.slug, city=city.slug),
    )

    assertContains(response, "Nenhum horário cadastrado.")


@pytest.mark.django_db
def test_filter_by_time(client: Client):
    city = baker.make(City)
    baker.make(
        Schedule, day=Schedule.Day.SUNDAY, start_time=time(9, 57), parish__city=city
    )
    sunday_afternoon = baker.make(
        Schedule, day=Schedule.Day.SUNDAY, start_time=time(14, 12), parish__city=city
    )

    response = client.get(
        resolve_url("by_city", state=city.state.slug, city=city.slug),
        data={"horario": "12"},
    )

    assertQuerySetEqual(
        response.context["schedules"],
        [sunday_afternoon],
    )


@pytest.mark.django_db
def test_filter_by_type_default_mass(client):
    city = baker.make(City)
    mass = baker.make(Schedule, parish__city=city, type=Schedule.Type.MASS)
    baker.make(Schedule, parish__city=city, type=Schedule.Type.CONFESSION)

    response = client.get(
        resolve_url("by_city", state=city.state.slug, city=city.slug),
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
    city = baker.make(City)
    baker.make(Schedule, parish__city=city, type=Schedule.Type.MASS)
    confession = baker.make(Schedule, parish__city=city, type=Schedule.Type.CONFESSION)

    response = client.get(
        resolve_url("by_city", state=city.state.slug, city=city.slug),
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
    city = baker.make(City)
    baker.make(
        Schedule,
        type=Schedule.Type.CONFESSION,
        start_time=time(9),
        end_time=time(11),
        parish__city=city,
    )

    response = client.get(
        resolve_url("by_city", state=city.state.slug, city=city.slug),
        data={"tipo": "confissoes"},
    )

    assertContains(response, "9:00")
    assertContains(response, "11:00")


@pytest.mark.django_db
def test_filter_by_end_time_if_exists(client: Client):
    city = baker.make(City)
    confession = baker.make(
        Schedule,
        type=Schedule.Type.CONFESSION,
        start_time=time(9),
        end_time=time(11),
        parish__city=city,
    )

    response = client.get(
        resolve_url("by_city", state=city.state.slug, city=city.slug),
        data={"tipo": "confissoes", "horario": "10"},
    )

    assertQuerySetEqual(response.context["schedules"], [confession])


@pytest.mark.django_db
def test_filter_by_verified(client: Client):
    city = baker.make(City)
    verified = baker.make(Schedule, parish__city=city, _fill_optional=["verified_at"])
    unverified = baker.make(Schedule, parish__city=city)

    response = client.get(
        resolve_url("by_city", state=city.state.slug, city=city.slug),
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
    city = baker.make(City)

    response = client.get(
        resolve_url("by_city", state=city.state.slug, city=city.slug),
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

    city = schedule.parish.city
    response = client.get(resolve_url("by_city", state=city.state.slug, city=city.slug))

    html = response.content.decode()
    assert source.description in html


@pytest.mark.django_db
def test_schedule_with_source_with_link(client):
    source = baker.make(Source, _fill_optional=["link"])
    schedule = baker.make(Schedule, source=source)

    city = schedule.parish.city
    response = client.get(resolve_url("by_city", state=city.state.slug, city=city.slug))

    html = response.content.decode()
    assert f'href="{source.link}"' in html


@pytest.mark.django_db
def test_verified_schedule(client):
    schedule = baker.make(Schedule, _fill_optional=["verified_at"])

    city = schedule.parish.city
    response = client.get(resolve_url("by_city", state=city.state.slug, city=city.slug))

    html = response.content.decode()
    assert f"Verificado por Missas.com.br em {schedule.verified_at:%d/%m/%Y}" in html


@pytest.mark.django_db
def test_schedule_with_location(client):
    schedule = baker.make(Schedule, _fill_optional=["location"])

    city = schedule.parish.city
    response = client.get(resolve_url("by_city", state=city.state.slug, city=city.slug))

    html = response.content.decode()
    assert schedule.location in html


@pytest.mark.django_db
def test_breadcrumb_to_state(client):
    schedule = baker.make(Schedule)

    city = schedule.parish.city
    response = client.get(resolve_url("by_city", state=city.state.slug, city=city.slug))

    html = response.content.decode()
    assert f'<a href="/{city.state.slug}">{city.state.name}</a>' in html


@pytest.mark.django_db
def test_number_of_queries(client, django_assert_max_num_queries):
    city = baker.make(City)
    baker.make(Schedule, parish__city=city, _quantity=100)

    with django_assert_max_num_queries(20):  # Increased for database cache queries
        response = client.get(
            resolve_url("by_city", state=city.state.slug, city=city.slug)
        )

    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_title(client):
    city = baker.make(City)

    response = client.get(resolve_url("by_city", state=city.state.slug, city=city.slug))

    assertInHTML(
        f"<title>Horários de missas e confissões em {city.name}/{city.state.short_name.upper()}</title>",
        response.content.decode(),
    )
