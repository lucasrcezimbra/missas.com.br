import requests
from model_bakery import baker

from missas.core.models import Contact, Parish


def test_real_http_scan_and_authorization(live_server, settings):
    settings.MISSAS_API_SHARED_SECRET = (
        "local-http-test-key"  # noqa: S105 - synthetic credential
    )
    parishes = baker.make(Parish, _quantity=2)
    Contact.objects.bulk_create(
        [Contact(parish=parish, whatsapp="+5511999990001") for parish in parishes]
    )
    endpoint = f"{live_server.url}/api/parishes"
    headers = {"X-API-Key": "local-http-test-key"}
    first = requests.get(endpoint, params={"limit": 1}, headers=headers, timeout=5)
    first.raise_for_status()
    page = first.json()
    second = requests.get(
        endpoint,
        params={"limit": 1, "cursor": page["next_cursor"]},
        headers=headers,
        timeout=5,
    )
    second.raise_for_status()
    following = second.json()
    denied = requests.get(endpoint, params={"limit": 1}, timeout=5)
    assert {
        "ids": [item["id"] for item in page["items"] + following["items"]],
        "next_cursor": following["next_cursor"],
        "anonymous_status": denied.status_code,
    } == {
        "ids": [parish.pk for parish in parishes],
        "next_cursor": None,
        "anonymous_status": 401,
    }
