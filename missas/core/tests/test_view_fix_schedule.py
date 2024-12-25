from http import HTTPStatus
from uuid import uuid4

import pytest
from django.shortcuts import resolve_url
from model_bakery import baker

from missas.core.models import Schedule, Source


@pytest.mark.django_db
def test_404_if_schedule_doesnt_exist(client):
    response = client.patch(resolve_url("fix_schedule", id=uuid4()))
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
@pytest.mark.parametrize("verb", ["get", "post", "delete", "put"])
def test_accepts_only_patch(verb, client):
    response = getattr(client, verb)(resolve_url("fix_schedule", id=uuid4()))
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_response(client):
    schedule = baker.make(Schedule)

    response = client.patch(resolve_url("fix_schedule", id=uuid4()))

    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_create_new_schedule_fix(client):
    schedule = baker.make(Schedule)

    response = client.patch(resolve_url("fix_schedule", id=uuid4()))

    schedule_fix = ScheduleFix.objects.get()
    assert schedule_fix == HTTPStatus.OK
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    day = models.IntegerField(choices=Day.choices)
    location = models.CharField(max_length=128, blank=True)
    observation = models.TextField(blank=True, default="")
    source = models.ForeignKey(Source, on_delete=models.RESTRICT, blank=True, null=True)
    start_time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True)
    type = models.CharField(choices=Type.choices, default=Type.MASS)
    schedule
