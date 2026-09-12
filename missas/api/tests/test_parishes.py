import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from freezegun import freeze_time
from model_bakery import baker

from missas.core.models import Contact, Location, Parish, Schedule, Source


@pytest.fixture
def authorized(client, settings):
    settings.MISSAS_API_SHARED_SECRET = (
        "test-api-secret"  # noqa: S105 - synthetic credential
    )
    client.defaults["HTTP_X_API_KEY"] = "test-api-secret"
    return client


@pytest.mark.django_db
def test_requires_shared_secret(client):
    response = client.get("/api/parishes")
    assert (response.status_code, response.json()) == (
        401,
        {"detail": "Não autorizado"},
    )


@pytest.mark.django_db
def test_lists_only_recorded_whatsapp_contacts_without_freshness_filter(authorized):
    fresh = baker.make(Parish)
    unknown = baker.make(Parish)
    baker.make(Contact, parish=fresh, whatsapp="+5511999990001")
    baker.make(Contact, parish=unknown, whatsapp="+5511999990002")
    baker.make(Schedule, parish=fresh, verified_at="2026-09-10")
    baker.make(Contact, parish=baker.make(Parish), phone="+5511999990003")
    baker.make(Contact, parish=baker.make(Parish), instagram="example")
    baker.make(Contact, parish=baker.make(Parish), whatsapp="  ")
    baker.make(Parish)
    response = authorized.get("/api/parishes")
    assert [item["id"] for item in response.json()["items"]] == [fresh.pk, unknown.pk]


@pytest.mark.django_db
def test_exposes_schedule_verification_and_source_separately_from_current_contact(
    authorized,
):
    parish = baker.make(
        Parish, name="São José", city__name="Natal", city__state__short_name="RN"
    )
    contact = baker.make(Contact, parish=parish, whatsapp="+5511999990001")
    source = baker.make(
        Source, type="whatsapp", description="Previous contributor", link=None
    )
    location = baker.make(Location, name="Matriz", address="Praça Central")
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
    unknown = baker.make(
        Schedule,
        parish=parish,
        day=1,
        start_time="09:00",
        end_time=None,
        verified_at=None,
        source=None,
        location=None,
        location_name="Capela",
    )
    baker.make(Schedule, parish=parish, type="confession", day=2)
    response = authorized.get("/api/parishes")
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
                        "location": {
                            "id": location.pk,
                            "name": "Matriz",
                            "address": "Praça Central",
                        },
                        "location_name": "",
                        "source": {
                            "id": source.pk,
                            "type": "whatsapp",
                            "description": "Previous contributor",
                            "link": None,
                        },
                    },
                    {
                        "id": unknown.pk,
                        "day": 1,
                        "start_time": "09:00:00",
                        "end_time": None,
                        "observation": "",
                        "verified_at": None,
                        "location": None,
                        "location_name": "Capela",
                        "source": None,
                    },
                ],
            }
        ],
        "next_cursor": None,
    }


@pytest.mark.django_db
@pytest.mark.parametrize(
    "secret,key",
    [
        ("", ""),
        ("", "supplied"),
        ("  ", "  "),
        ("configured", "wrong"),
        ("configured", ""),
    ],
)
def test_fails_closed(client, settings, secret, key):
    settings.MISSAS_API_SHARED_SECRET = secret
    response = client.get("/api/parishes", HTTP_X_API_KEY=key)
    assert (response.status_code, response.json()) == (
        401,
        {"detail": "Não autorizado"},
    )


@pytest.mark.django_db
def test_authorized_response_cannot_bypass_auth_through_site_cache(authorized):
    response = authorized.get("/api/parishes")
    del authorized.defaults["HTTP_X_API_KEY"]
    denied = authorized.get("/api/parishes")
    assert ("no-store" in response.get("Cache-Control", ""), denied.status_code) == (
        True,
        401,
    )


@pytest.mark.django_db
def test_paginates_in_stable_id_order(authorized):
    first = baker.make(Parish)
    second = baker.make(Parish)
    baker.make(Contact, parish=first, whatsapp="+5511999990001")
    baker.make(Contact, parish=second, whatsapp="+5511999990002")
    page = authorized.get("/api/parishes", {"limit": 1}).json()
    following = authorized.get(
        "/api/parishes", {"limit": 1, "cursor": page["next_cursor"]}
    ).json()
    assert (
        [item["id"] for item in page["items"]],
        [item["id"] for item in following["items"]],
        following["next_cursor"],
    ) == ([first.pk], [second.pk], None)


@pytest.mark.django_db
@pytest.mark.parametrize("change", ["delete", "add", "gain_contact", "lose_contact"])
def test_membership_changes_require_restart_instead_of_silent_gaps(authorized, change):
    older_without_contact = baker.make(Parish)
    first = baker.make(Parish)
    second = baker.make(Parish)
    contact = baker.make(Contact, parish=first, whatsapp="+5511999990001")
    baker.make(Contact, parish=second, whatsapp="+5511999990002")
    page = authorized.get("/api/parishes", {"limit": 1}).json()
    if change == "delete":
        first.delete()
    elif change == "add":
        baker.make(Contact, parish=baker.make(Parish), whatsapp="+5511999990003")
    elif change == "gain_contact":
        # Existing older IDs can enter behind the cursor, not just at the end.
        baker.make(Contact, parish=older_without_contact, whatsapp="+5511999990003")
    else:
        contact.whatsapp = ""
        contact.save()
    response = authorized.get(
        "/api/parishes", {"limit": 1, "cursor": page["next_cursor"]}
    )
    assert (response.status_code, response.json()) == (
        409,
        {"detail": "A lista mudou; reinicie a paginação"},
    )


@pytest.mark.django_db
@pytest.mark.parametrize("cursor", ["", "invalid", "not:a:signature"])
def test_invalid_cursor_is_a_client_error(authorized, cursor):
    response = authorized.get("/api/parishes", {"cursor": cursor})
    assert (response.status_code, response.json()) == (
        400,
        {"detail": "Cursor inválido ou expirado"},
    )


@pytest.mark.django_db
@pytest.mark.parametrize("limit", [0, -1, 101, "invalid"])
def test_page_size_is_bounded(authorized, limit):
    response = authorized.get("/api/parishes", {"limit": limit})
    assert response.status_code == 422


@pytest.mark.django_db
def test_cursor_expires(authorized):
    parishes = baker.make(Parish, _quantity=2)
    Contact.objects.bulk_create(
        [Contact(parish=parish, whatsapp="+5511999990001") for parish in parishes]
    )
    with freeze_time("2026-09-10 10:00:00"):
        page = authorized.get("/api/parishes", {"limit": 1}).json()
    with freeze_time("2026-09-10 11:00:01"):
        response = authorized.get("/api/parishes", {"cursor": page["next_cursor"]})
    assert (response.status_code, response.json()) == (
        400,
        {"detail": "Cursor inválido ou expirado"},
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "headers,query",
    [
        ({"HTTP_AUTHORIZATION": "Bearer test-api-secret"}, {}),
        ({}, {"api_key": "test-api-secret"}),
    ],
)
def test_does_not_accept_bearer_or_query_credentials(client, settings, headers, query):
    settings.MISSAS_API_SHARED_SECRET = (
        "test-api-secret"  # noqa: S105 - synthetic credential
    )
    response = client.get("/api/parishes", query, **headers)
    assert response.status_code == 401


@pytest.mark.django_db
@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_has_no_write_methods(authorized, method):
    response = getattr(authorized, method)("/api/parishes", data={})
    assert response.status_code == 405


@pytest.mark.django_db
def test_request_performs_no_database_writes(authorized):
    parish = baker.make(Parish)
    baker.make(Contact, parish=parish, whatsapp="+5511999990001")
    baker.make(Schedule, parish=parish, verified_at="2025-01-02")
    with CaptureQueriesContext(connection) as queries:
        response = authorized.get("/api/parishes")
    assert response.status_code == 200
    assert all(
        query["sql"].split()[0] in {"SELECT", "SAVEPOINT", "RELEASE", "BEGIN", "COMMIT"}
        for query in queries
    )


@pytest.mark.django_db
@pytest.mark.parametrize("count", [1, 20])
def test_query_count_does_not_grow_with_page_size(
    authorized, django_assert_num_queries, count
):
    parishes = baker.make(Parish, _quantity=count)
    Contact.objects.bulk_create(
        [Contact(parish=parish, whatsapp="+5511999990001") for parish in parishes]
    )
    Schedule.objects.bulk_create(
        [Schedule(parish=parish, day=0, start_time="08:00") for parish in parishes]
    )
    with django_assert_num_queries(5):
        response = authorized.get("/api/parishes")
    assert len(response.json()["items"]) == count


@pytest.mark.django_db
def test_default_page_size_is_one_hundred(authorized):
    parishes = baker.make(Parish, _quantity=101)
    Contact.objects.bulk_create(
        [Contact(parish=parish, whatsapp="+5511999990001") for parish in parishes]
    )
    page = authorized.get("/api/parishes").json()
    following = authorized.get("/api/parishes", {"cursor": page["next_cursor"]}).json()
    assert (
        len(page["items"]),
        [item["id"] for item in following["items"]],
        following["next_cursor"],
    ) == (100, [parishes[-1].pk], None)


@pytest.mark.django_db
def test_errors_do_not_expose_secret(authorized, caplog):
    response = authorized.get("/api/parishes", {"cursor": "invalid"})
    assert "test-api-secret" not in response.content.decode() + caplog.text
