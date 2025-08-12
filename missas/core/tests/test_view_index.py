from datetime import date
from http import HTTPStatus

import pytest
from django.shortcuts import resolve_url
from model_bakery import baker
from pytest_django.asserts import assertContains, assertTemplateUsed

from missas.core.models import City, Parish, Schedule, Source, State


@pytest.mark.django_db
def test_status_code_and_template(client):
    response = client.get(resolve_url("index"))

    assert response.status_code == HTTPStatus.OK
    assertTemplateUsed(response, "home.html")


@pytest.mark.django_db
def test_page_title_and_content(client):
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
def test_statistics_with_no_data(client):
    response = client.get(resolve_url("index"))

    stats = response.context["stats"]
    assert stats["cities_with_parishes"] == 0
    assert stats["parishes"] == 0
    assert stats["schedules"] == 0
    assert stats["verified_schedules"] == 0

    assertContains(response, ">0</h4>", count=4)


@pytest.mark.django_db
def test_statistics_with_data(client):
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
def test_states_with_cities_display(client):
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
def test_states_with_many_cities_show_all(client):
    """Test that states show all their cities (no truncation)"""
    state = baker.make(State)
    cities = baker.make(City, state=state, _quantity=8)
    parishes = [baker.make(Parish, city=c) for c in cities]
    [baker.make(Schedule, parish=p) for p in parishes]

    response = client.get(resolve_url("index"))

    for c in cities:
        assertContains(response, c.name)


@pytest.mark.django_db
def test_query_count_optimization(client, django_assert_num_queries):
    """Test that the view doesn't perform excessive database queries"""
    state1 = baker.make(State)
    state2 = baker.make(State)

    city1 = baker.make(City, state=state1)
    city2 = baker.make(City, state=state2)

    parish1 = baker.make(Parish, city=city1)
    parish2 = baker.make(Parish, city=city2)

    baker.make(Schedule, parish=parish1)
    baker.make(Schedule, parish=parish2)

    with django_assert_num_queries(num=6):
        response = client.get(resolve_url("index"))

    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_only_shows_states_with_schedules(client):
    """Test that only states with cities that have parishes with schedules are shown"""
    # Create state with schedules
    state_with_schedules = baker.make(State, name="Estado com Horários")
    city_with_schedules = baker.make(City, state=state_with_schedules)
    parish_with_schedules = baker.make(Parish, city=city_with_schedules)
    baker.make(Schedule, parish=parish_with_schedules)

    # Create state with parishes but no schedules
    state_with_parishes_no_schedules = baker.make(State, name="Estado sem Horários")
    city_with_parishes_no_schedules = baker.make(
        City, state=state_with_parishes_no_schedules
    )
    baker.make(Parish, city=city_with_parishes_no_schedules)  # Parish without schedules

    # Create state with no parishes
    state_without_parishes = baker.make(State, name="Estado sem Paróquias")
    baker.make(City, state=state_without_parishes)  # City without parishes

    response = client.get(resolve_url("index"))

    states_with_cities = response.context["states_with_cities"]
    state_names = [state.name for state in states_with_cities]

    # Only state with schedules should appear
    assert "Estado com Horários" in state_names
    assert "Estado sem Horários" not in state_names
    assert "Estado sem Paróquias" not in state_names
    assert len(states_with_cities) == 1
