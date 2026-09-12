import pytest
from django.core.cache import cache
from model_bakery import baker

from missas.core.models import Contact, Location, Parish, Schedule, Source


@pytest.fixture(autouse=True)
def clear_site_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
def test_is_public(client):
    response = client.get("/api/v0/parishes")
    assert (response.status_code, response.json()) == (200, {"items": [], "count": 0})


@pytest.mark.django_db
def test_lists_only_recorded_whatsapp_contacts_without_freshness_filter(client):
    fresh = baker.make(Parish)
    unknown = baker.make(Parish)
    baker.make(Contact, parish=fresh, whatsapp="+5511999990001")
    baker.make(Contact, parish=unknown, whatsapp="+5511999990002")
    baker.make(Schedule, parish=fresh, verified_at="2026-09-10")
    baker.make(Contact, parish=baker.make(Parish), phone="+5511999990003")
    baker.make(Contact, parish=baker.make(Parish), instagram="example")
    baker.make(Contact, parish=baker.make(Parish), whatsapp="  ")
    baker.make(Parish)
    response = client.get("/api/v0/parishes")
    assert [item["id"] for item in response.json()["items"]] == [fresh.pk, unknown.pk]


@pytest.mark.django_db
def test_exposes_fields_and_filters_and_orders_mass_schedules(client):
    parish = baker.make(
        Parish, name="São José", city__name="Natal", city__state__short_name="RN"
    )
    contact = baker.make(Contact, parish=parish, whatsapp="+5511999990001")
    source = baker.make(
        Source, type="whatsapp", description="Previous contributor", link=None
    )
    location = baker.make(Location, name="Matriz", address="Praça Central")
    later = baker.make(
        Schedule,
        parish=parish,
        day=1,
        start_time="09:00",
        source=None,
        location=None,
        location_name="Capela",
        verified_at=None,
    )
    mass = baker.make(
        Schedule,
        parish=parish,
        day=0,
        start_time="08:00",
        end_time=None,
        verified_at="2025-01-02",
        source=source,
        location=location,
    )
    baker.make(Schedule, parish=parish, type="confession", day=2)

    response = client.get("/api/v0/parishes")

    assert response.json() == {
        "items": [
            {
                "id": parish.pk,
                "name": "São José",
                "city": "Natal",
                "state": "RN",
                "contact": {"id": contact.pk, "whatsapp": "+5511999990001"},
                "mass_schedules": [
                    {
                        "id": mass.pk,
                        "day": 0,
                        "start_time": "08:00:00",
                        "end_time": None,
                        "observation": "",
                        "verified_at": "2025-01-02",
                        "location_name": "",
                        "location": {
                            "id": location.pk,
                            "name": "Matriz",
                            "address": "Praça Central",
                        },
                        "source": {
                            "id": source.pk,
                            "type": "whatsapp",
                            "description": "Previous contributor",
                            "link": None,
                        },
                    },
                    {
                        "id": later.pk,
                        "day": 1,
                        "start_time": "09:00:00",
                        "end_time": None,
                        "observation": "",
                        "verified_at": None,
                        "location_name": "Capela",
                        "location": None,
                        "source": None,
                    },
                ],
            }
        ],
        "count": 1,
    }


@pytest.mark.django_db
def test_limit_offset_pagination_is_ordered_by_id(client):
    parishes = baker.make(Parish, _quantity=3)
    Contact.objects.bulk_create(
        [Contact(parish=parish, whatsapp="+5511999990001") for parish in parishes]
    )
    response = client.get("/api/v0/parishes", {"limit": 1, "offset": 1})
    assert response.json() == {
        "items": [
            {
                "id": parishes[1].pk,
                "name": parishes[1].name,
                "city": parishes[1].city.name,
                "state": parishes[1].city.state.short_name,
                "contact": {
                    "id": parishes[1].contact.pk,
                    "whatsapp": "+5511999990001",
                },
                "mass_schedules": [],
            }
        ],
        "count": 3,
    }


@pytest.mark.django_db
@pytest.mark.parametrize(
    "query", [{"limit": 0}, {"limit": -1}, {"offset": -1}, {"limit": "x"}]
)
def test_invalid_pagination_is_rejected(client, query):
    assert client.get("/api/v0/parishes", query).status_code == 422


@pytest.mark.django_db
def test_limit_is_capped_at_one_hundred(client):
    parishes = baker.make(Parish, _quantity=101)
    Contact.objects.bulk_create(
        [Contact(parish=parish, whatsapp="+5511999990001") for parish in parishes]
    )
    body = client.get("/api/v0/parishes", {"limit": 101}).json()
    assert (len(body["items"]), body["count"]) == (100, 101)


@pytest.mark.django_db
def test_site_cache_serves_api_response_and_separates_query_strings(client):
    first, second = baker.make(Parish, _quantity=2)
    baker.make(Contact, parish=first, whatsapp="+5511999990001")
    baker.make(Contact, parish=second, whatsapp="+5511999990002")
    first_page = client.get("/api/v0/parishes", {"limit": 1, "offset": 0})
    first.name = "Changed after response was cached"
    first.save()

    cached = client.get("/api/v0/parishes", {"limit": 1, "offset": 0})
    other_page = client.get("/api/v0/parishes", {"limit": 1, "offset": 1})

    assert cached.content == first_page.content
    assert cached["Age"] == "0"
    assert [item["id"] for item in other_page.json()["items"]] == [second.pk]
    assert "max-age=86400" in first_page["Cache-Control"]


@pytest.mark.django_db
@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_has_no_write_methods(client, method):
    response = getattr(client, method)("/api/v0/parishes", data={})
    assert response.status_code == 405


@pytest.mark.django_db
@pytest.mark.parametrize("count", [1, 20])
def test_query_count_does_not_grow_with_page_size(
    client, django_assert_num_queries, count
):
    parishes = baker.make(Parish, _quantity=count)
    Contact.objects.bulk_create(
        [Contact(parish=parish, whatsapp="+5511999990001") for parish in parishes]
    )
    Schedule.objects.bulk_create(
        [Schedule(parish=parish, day=0, start_time="08:00") for parish in parishes]
    )
    # Includes the database-backed site cache reads and writes.
    with django_assert_num_queries(14):
        response = client.get("/api/v0/parishes")
    assert len(response.json()["items"]) == count
