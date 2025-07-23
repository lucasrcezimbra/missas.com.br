from datetime import date
from http import HTTPStatus

import pytest
from django.shortcuts import resolve_url
from django.test import override_settings
from model_bakery import baker
from pytest_django.asserts import assertContains, assertTemplateUsed

from missas.core.models import City, Parish, Schedule, Source, State


@pytest.mark.django_db
def test_index_status_code_and_template(client):
    response = client.get(resolve_url("index"))

    assert response.status_code == HTTPStatus.OK
    assertTemplateUsed(response, "home.html")


@pytest.mark.django_db
def test_index_page_title_and_content(client):
    response = client.get(resolve_url("index"))

    assertContains(
        response,
        "<title>Missas.com.br - Horários de missas e confissões no Brasil</title>",
        html=True,
    )
    assertContains(response, "Bem-vindo ao Missas.com.br")
    assertContains(response, "Nossos Números")
    assertContains(response, "Estados e Cidades com Paróquias")
    assertContains(response, "Adicione uma Paróquia")
    assertContains(response, "Projeto Open Source")


@pytest.mark.django_db
def test_index_statistics_with_no_data(client):
    response = client.get(resolve_url("index"))

    stats = response.context["stats"]
    assert stats["cities_with_parishes"] == 0
    assert stats["parishes"] == 0
    assert stats["schedules"] == 0
    assert stats["verified_schedules"] == 0

    assertContains(response, ">0</h4>", count=4)


@pytest.mark.django_db
def test_index_statistics_with_data(client):
    # Create test data
    state1 = baker.make(State, name="Rio Grande do Norte", slug="rn")
    state2 = baker.make(State, name="São Paulo", slug="sp")

    city1 = baker.make(City, name="Natal", slug="natal", state=state1)
    city2 = baker.make(City, name="Mossoró", slug="mossoro", state=state1)
    city3 = baker.make(City, name="São Paulo", slug="sao-paulo", state=state2)
    # City without parishes to test filtering
    baker.make(City, name="Campinas", slug="campinas", state=state2)

    parish1 = baker.make(
        Parish, name="Paróquia Nossa Senhora", slug="nossa-senhora", city=city1
    )
    parish2 = baker.make(Parish, name="Paróquia São José", slug="sao-jose", city=city2)
    parish3 = baker.make(Parish, name="Catedral da Sé", slug="catedral-se", city=city3)

    source = baker.make(Source)

    # Create schedules (some verified, some not)
    baker.make(
        Schedule,
        parish=parish1,
        type=Schedule.Type.MASS,
        verified_at=date.today(),
        source=source,
    )
    baker.make(
        Schedule,
        parish=parish1,
        type=Schedule.Type.CONFESSION,
        verified_at=None,
        source=source,
    )
    baker.make(
        Schedule,
        parish=parish2,
        type=Schedule.Type.MASS,
        verified_at=date.today(),
        source=source,
    )
    baker.make(
        Schedule,
        parish=parish3,
        type=Schedule.Type.MASS,
        verified_at=None,
        source=source,
    )
    baker.make(
        Schedule,
        parish=parish3,
        type=Schedule.Type.CONFESSION,
        verified_at=date.today(),
        source=source,
    )

    response = client.get(resolve_url("index"))

    stats = response.context["stats"]
    assert stats["cities_with_parishes"] == 3  # city4 has no parishes with schedules
    assert stats["parishes"] == 3
    assert stats["schedules"] == 5
    assert stats["verified_schedules"] == 3

    assertContains(
        response, "3</h4>"
    )  # Should appear for cities, parishes, and verified schedules
    assertContains(response, "5</h4>")  # Should appear for total schedules


@pytest.mark.django_db
def test_index_states_with_cities_display(client):
    # Create test data
    state1 = baker.make(State, name="Rio Grande do Norte", slug="rn")
    state2 = baker.make(State, name="São Paulo", slug="sp")
    # State without parishes to test filtering
    baker.make(State, name="Minas Gerais", slug="mg")

    city1 = baker.make(City, name="Natal", slug="natal", state=state1)
    city2 = baker.make(City, name="Mossoró", slug="mossoro", state=state1)
    city3 = baker.make(City, name="São Paulo", slug="sao-paulo", state=state2)

    parish1 = baker.make(
        Parish, name="Paróquia Nossa Senhora", slug="nossa-senhora", city=city1
    )
    parish2 = baker.make(Parish, name="Paróquia São José", slug="sao-jose", city=city2)
    parish3 = baker.make(Parish, name="Catedral da Sé", slug="catedral-se", city=city3)

    source = baker.make(Source)
    baker.make(Schedule, parish=parish1, source=source)
    baker.make(Schedule, parish=parish2, source=source)
    baker.make(Schedule, parish=parish3, source=source)

    response = client.get(resolve_url("index"))

    states_with_cities = response.context["states_with_cities"]
    assert len(states_with_cities) == 2  # Only states with parishes that have schedules

    state_names = [state.name for state in states_with_cities]
    assert "Rio Grande do Norte" in state_names
    assert "São Paulo" in state_names
    assert "Minas Gerais" not in state_names

    assertContains(response, "Rio Grande do Norte")
    assertContains(response, "São Paulo")
    assertContains(response, "Natal")
    assertContains(response, "Mossoró")


@pytest.mark.django_db
def test_index_states_with_many_cities_show_all(client):
    """Test that states show all their cities (no truncation)"""
    state = baker.make(State, name="São Paulo", slug="sp")

    # Create 8 cities with parishes and schedules
    cities = []
    for i in range(8):
        city = baker.make(City, name=f"Cidade {i+1}", slug=f"cidade-{i+1}", state=state)
        parish = baker.make(
            Parish, name=f"Paróquia {i+1}", slug=f"paroquia-{i+1}", city=city
        )
        source = baker.make(Source)
        baker.make(Schedule, parish=parish, source=source)
        cities.append(city)

    response = client.get(resolve_url("index"))

    # Should show all 8 cities
    for i in range(8):
        assertContains(response, f"Cidade {i+1}")

    # Should not show truncation message
    assert "... e mais" not in response.content.decode()


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_index_query_count_optimization(client, django_assert_num_queries):
    """Test that the view doesn't perform excessive database queries"""
    # Create test data
    state1 = baker.make(State, name="Rio Grande do Norte", slug="rn")
    state2 = baker.make(State, name="São Paulo", slug="sp")

    city1 = baker.make(City, name="Natal", slug="natal", state=state1)
    city2 = baker.make(City, name="São Paulo", slug="sao-paulo", state=state2)

    parish1 = baker.make(Parish, name="Paróquia 1", slug="paroquia-1", city=city1)
    parish2 = baker.make(Parish, name="Paróquia 2", slug="paroquia-2", city=city2)

    source = baker.make(Source)
    baker.make(Schedule, parish=parish1, source=source)
    baker.make(Schedule, parish=parish2, source=source)

    # The view should use a reasonable number of queries:
    # 1. Count cities with parishes that have schedules
    # 2. Count parishes
    # 3. Count schedules
    # 4. Count verified schedules
    # 5. Get all states
    # 6-7. For each state, check if it has cities with schedules (exists query)
    # 8-9. For each state with cities, get the actual cities (annotated query)
    with django_assert_num_queries(num=9):  # Actual number based on test output
        response = client.get(resolve_url("index"))

    assert response.status_code == HTTPStatus.OK
