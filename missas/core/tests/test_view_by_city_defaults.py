from datetime import datetime as dt
from datetime import time
from http import HTTPStatus
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest
from django.shortcuts import resolve_url
from model_bakery import baker

from missas.core.models import City, Schedule


@pytest.mark.django_db
def test_no_params_adds_defaults_and_hx_replace_url_header(client):
    """When no query params are provided, should add default tipo, dia, and horario"""
    city = baker.make(City)

    # Mock the current time to Thursday, October 16, 2025 at 21:00 (Brazil time)
    mock_time = dt(2025, 10, 16, 21, 0, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))

    with patch("django.utils.timezone.now") as mock_now:
        mock_now.return_value = mock_time
        response = client.get(
            resolve_url("by_city", state=city.state.slug, city=city.slug),
        )

    assert response.status_code == HTTPStatus.OK
    # Should set HX-Replace-Url header with default params
    assert "HX-Replace-Url" in response.headers
    # Current day in Brazil is Thursday (quinta in Portuguese)
    assert "dia=quinta" in response["HX-Replace-Url"]
    assert "tipo=missas" in response["HX-Replace-Url"]
    assert "horario=21" in response["HX-Replace-Url"]


@pytest.mark.django_db
def test_only_tipo_param_adds_dia_and_horario_defaults(client):
    """When only tipo param is provided, should add dia and horario defaults"""
    city = baker.make(City)

    # Mock the current time to Friday, October 17, 2025 at 14:00 (Brazil time)
    mock_time = dt(2025, 10, 17, 14, 0, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))

    with patch("django.utils.timezone.now") as mock_now:
        mock_now.return_value = mock_time
        response = client.get(
            resolve_url("by_city", state=city.state.slug, city=city.slug),
            data={"tipo": "missas"},
        )

    assert response.status_code == HTTPStatus.OK
    # Should set HX-Replace-Url header with default dia and horario
    assert "HX-Replace-Url" in response.headers
    # Current day in Brazil is Friday (sexta in Portuguese)
    assert "dia=sexta" in response["HX-Replace-Url"]
    assert "tipo=missas" in response["HX-Replace-Url"]
    assert "horario=14" in response["HX-Replace-Url"]


@pytest.mark.django_db
def test_with_dia_param_does_not_add_defaults(client):
    """When dia param is provided, should NOT add defaults"""
    city = baker.make(City)

    response = client.get(
        resolve_url("by_city", state=city.state.slug, city=city.slug),
        data={"dia": "domingo"},
    )

    assert response.status_code == HTTPStatus.OK
    # Should NOT set HX-Replace-Url header when dia is already provided
    assert "HX-Replace-Url" not in response.headers


@pytest.mark.django_db
def test_with_horario_param_does_not_add_defaults(client):
    """When horario param is provided, should NOT add defaults"""
    city = baker.make(City)

    response = client.get(
        resolve_url("by_city", state=city.state.slug, city=city.slug),
        data={"horario": "10"},
    )

    assert response.status_code == HTTPStatus.OK
    # Should NOT set HX-Replace-Url header when horario is already provided
    assert "HX-Replace-Url" not in response.headers


@pytest.mark.django_db
def test_with_all_params_does_not_add_defaults(client):
    """When all params are provided, should NOT add defaults"""
    city = baker.make(City)

    response = client.get(
        resolve_url("by_city", state=city.state.slug, city=city.slug),
        data={"tipo": "missas", "dia": "domingo", "horario": "10"},
    )

    assert response.status_code == HTTPStatus.OK
    # Should NOT set HX-Replace-Url header when all params are already provided
    assert "HX-Replace-Url" not in response.headers


@pytest.mark.django_db
def test_defaults_with_brazilian_timezone(client):
    """Should use Brazilian timezone (America/Sao_Paulo) for defaults"""
    city = baker.make(City)

    # Create a time that is different in UTC vs Brazil time
    # Sunday 2025-10-19 02:59 UTC = Saturday 2025-10-18 23:59 BRT (UTC-3)
    mock_time_utc = dt(2025, 10, 19, 2, 59, 0, tzinfo=ZoneInfo("UTC"))

    with patch("django.utils.timezone.now") as mock_now:
        mock_now.return_value = mock_time_utc
        response = client.get(
            resolve_url("by_city", state=city.state.slug, city=city.slug),
        )

    assert response.status_code == HTTPStatus.OK
    # Should use Brazilian time (Saturday 23:59), not UTC time (Sunday 02:59)
    assert "dia=sabado" in response["HX-Replace-Url"]
    assert "horario=23" in response["HX-Replace-Url"]


@pytest.mark.django_db
def test_defaults_filter_schedules_correctly(client):
    """Defaults should properly filter schedules by current day and hour"""
    city = baker.make(City)

    # Mock the current time to Wednesday at 14:00 (Brazil time)
    mock_time = dt(2025, 10, 15, 14, 0, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))

    # Create schedules for Wednesday
    wed_morning = baker.make(
        Schedule,
        parish__city=city,
        day=Schedule.Day.WEDNESDAY,
        start_time=time(9, 0),
        type=Schedule.Type.MASS,
    )
    wed_afternoon = baker.make(
        Schedule,
        parish__city=city,
        day=Schedule.Day.WEDNESDAY,
        start_time=time(18, 0),
        type=Schedule.Type.MASS,
    )
    # Create schedule for Thursday (should not appear)
    baker.make(
        Schedule,
        parish__city=city,
        day=Schedule.Day.THURSDAY,
        start_time=time(18, 0),
        type=Schedule.Type.MASS,
    )

    with patch("django.utils.timezone.now") as mock_now:
        mock_now.return_value = mock_time
        response = client.get(
            resolve_url("by_city", state=city.state.slug, city=city.slug),
        )

    # Should only show Wednesday schedules with start_time >= 14:00 or end_time >= 14:00
    # wed_morning (9:00) should not appear since it's before 14:00 and has no end_time
    # wed_afternoon (18:00) should appear since it's after 14:00
    assert response.status_code == HTTPStatus.OK
    assert wed_afternoon.parish.name in response.content.decode()
    assert wed_morning.parish.name not in response.content.decode()
