from datetime import datetime, timedelta
from http import HTTPStatus

from django.shortcuts import resolve_url
from freezegun import freeze_time

weekdays = ("segunda", "terca", "quarta", "quinta", "sexta", "sabado", "domingo")


def test_redirect(client):
    now = datetime.utcnow() - timedelta(hours=3)
    weekday = weekdays[now.weekday()]

    response = client.get(resolve_url("index"))

    assert response.status_code == HTTPStatus.FOUND
    assert (
        response.url
        == resolve_url("by_city", state="rio-grande-do-norte", city="natal")
        + f"?dia={weekday}"
        + f"&horario={now.hour}"
    )


@freeze_time("2023-11-19 10:00:00")
def test_redirect_sunday(client):
    response = client.get(resolve_url("index"))

    assert response.status_code == HTTPStatus.FOUND
    assert (
        response.url
        == resolve_url("by_city", state="rio-grande-do-norte", city="natal")
        + "?dia=domingo"
        + "&horario=7"
    )
