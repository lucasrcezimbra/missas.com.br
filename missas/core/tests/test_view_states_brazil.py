from http import HTTPStatus

import pytest
from django.shortcuts import resolve_url
from model_bakery import baker
from pytest_django.asserts import (
    assertContains,
    assertTemplateUsed,
)

from missas.core.models import City, Parish, State


@pytest.mark.django_db
def test_view_states_brazil(client):
    response = client.get(resolve_url("states_brazil"))
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_template(client):
    response = client.get(resolve_url("states_brazil"))
    assertTemplateUsed(response, "states_brazil.html")


@pytest.mark.django_db
def test_all_states(client):
    state1 = baker.make(State, name="State 1", short_name="S1")
    state2 = baker.make(State, name="State 2", short_name="S2")

    response = client.get(resolve_url("states_brazil"))

    assertContains(response, state1.name)
    assertContains(response, state1.short_name)
    assertContains(response, state2.name)
    assertContains(response, state2.short_name)


@pytest.mark.django_db
def test_states_with_parishes_count(client):
    state1 = baker.make(State, name="State 1", short_name="S1")
    state2 = baker.make(State, name="State 2", short_name="S2")

    # Create cities and parishes for state1
    city1 = baker.make(City, state=state1)
    parish1 = baker.make(Parish, city=city1)
    parish2 = baker.make(Parish, city=city1)

    # Create city but no parishes for state2
    city2 = baker.make(City, state=state2)

    response = client.get(resolve_url("states_brazil"))

    # State1 should show 2 parishes
    assertContains(response, "2 paróquias")
    # State2 should show "Sem paróquias"
    assertContains(response, "Sem paróquias")


@pytest.mark.django_db
def test_order_by_parishes_count_and_name(client):
    state1 = baker.make(State, name="State A", short_name="SA")
    state2 = baker.make(State, name="State B", short_name="SB")
    state3 = baker.make(State, name="State C", short_name="SC")

    # Create parishes for state2 (should be first)
    city2 = baker.make(City, state=state2)
    baker.make(Parish, city=city2, _quantity=3)

    # Create parishes for state1 (should be second)
    city1 = baker.make(City, state=state1)
    baker.make(Parish, city=city1, _quantity=2)

    # No parishes for state3 (should be last)

    response = client.get(resolve_url("states_brazil"))

    content = response.content.decode()
    # Check that state2 appears before state1, and state1 appears before state3
    assert (
        content.index(state2.name)
        < content.index(state1.name)
        < content.index(state3.name)
    )


@pytest.mark.django_db
def test_title(client):
    response = client.get(resolve_url("states_brazil"))
    assertContains(response, "<h1")
    assertContains(response, "Estados do Brasil")
