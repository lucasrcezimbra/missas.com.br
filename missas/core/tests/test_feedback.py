from http import HTTPStatus

import pytest
from django.shortcuts import resolve_url
from model_bakery import baker
from pytest_django.asserts import assertContains

from missas.core.models import Feedback, Parish


@pytest.mark.django_db
def test_create_feedback_without_parish(client):
    """Test creating feedback without parish reference"""
    response = client.post(
        resolve_url("create_feedback"),
        data={
            "message": "Horário está incorreto",
            "contact": "test@example.com",
        },
    )

    assert response.status_code == HTTPStatus.FOUND
    assert Feedback.objects.count() == 1

    feedback = Feedback.objects.first()
    assert feedback.message == "Horário está incorreto"
    assert feedback.contact == "test@example.com"
    assert feedback.parish is None


@pytest.mark.django_db
def test_create_feedback_with_parish(client):
    """Test creating feedback with parish reference"""
    parish = baker.make(Parish)

    response = client.post(
        resolve_url("create_feedback"),
        data={
            "message": "Endereço está errado",
            "contact": "+5584999999999",
            "parish_id": parish.id,
        },
    )

    assert response.status_code == HTTPStatus.FOUND
    assert Feedback.objects.count() == 1

    feedback = Feedback.objects.first()
    assert feedback.message == "Endereço está errado"
    assert feedback.contact == "+5584999999999"
    assert feedback.parish == parish


@pytest.mark.django_db
def test_create_feedback_without_message(client):
    """Test that feedback without message returns error via HTMX"""
    response = client.post(
        resolve_url("create_feedback"),
        data={"message": "", "contact": "test@example.com"},
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == HTTPStatus.OK
    assertContains(response, "Por favor, descreva o problema")
    assert Feedback.objects.count() == 0


@pytest.mark.django_db
def test_create_feedback_htmx_success(client):
    """Test successful feedback submission via HTMX"""
    response = client.post(
        resolve_url("create_feedback"),
        data={"message": "Teste de problema", "contact": ""},
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == HTTPStatus.OK
    assertContains(response, "Obrigado pelo seu feedback!")
    assert Feedback.objects.count() == 1


@pytest.mark.django_db
def test_create_feedback_only_accepts_post(client):
    """Test that only POST requests are accepted"""
    response = client.get(resolve_url("create_feedback"))
    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


@pytest.mark.django_db
def test_feedback_model_str_with_parish():
    """Test Feedback model __str__ with parish"""
    parish = baker.make(Parish, name="Paróquia Teste")
    feedback = baker.make(Feedback, parish=parish, message="Problema de teste aqui")

    assert str(feedback) == "Feedback sobre Paróquia Teste - Problema de teste aqui"


@pytest.mark.django_db
def test_feedback_model_str_without_parish():
    """Test Feedback model __str__ without parish"""
    feedback = baker.make(
        Feedback,
        parish=None,
        message="Problema geral muito longo que precisa ser truncado para o str",
    )

    assert str(feedback).startswith(
        "Feedback - Problema geral muito longo que precisa ser trunc"
    )


@pytest.mark.django_db
def test_feedback_with_invalid_parish_id(client):
    """Test that feedback is created even with invalid parish_id"""
    response = client.post(
        resolve_url("create_feedback"),
        data={
            "message": "Problema encontrado",
            "parish_id": 99999,
        },
    )

    assert response.status_code == HTTPStatus.FOUND
    assert Feedback.objects.count() == 1

    feedback = Feedback.objects.first()
    assert feedback.parish is None
