from http import HTTPStatus

import pytest
from django.shortcuts import resolve_url
from pytest_django.asserts import assertContains, assertTemplateUsed


@pytest.mark.django_db
@pytest.mark.parametrize(
    "path",
    ["/missing/path/with/extra/segments/", "/missing-state/"],
)
def test_not_found_page(client, settings, path):
    settings.DEBUG = False

    response = client.get(path)

    assert response.status_code == HTTPStatus.NOT_FOUND
    assertTemplateUsed(response, "404.html")
    assertContains(
        response,
        "<title>Página não encontrada - Missas.com.br</title>",
        status_code=404,
        html=True,
    )
    assertContains(response, "Página não encontrada", status_code=404)
    assertContains(
        response,
        f'<a href="{resolve_url("index")}" class="btn btn-primary btn-lg" hx-boost="false">'
        '<i class="fa-solid fa-house me-2" aria-hidden="true"></i> Voltar ao início</a>',
        status_code=404,
        html=True,
    )
