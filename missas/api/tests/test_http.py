import requests
from model_bakery import baker

from missas.core.models import Contact, Parish


def test_real_http_scan_is_public(live_server):
    parishes = baker.make(Parish, _quantity=2)
    Contact.objects.bulk_create(
        [Contact(parish=parish, whatsapp="+5511999990001") for parish in parishes]
    )
    endpoint = f"{live_server.url}/api/v0/parishes"
    first = requests.get(endpoint, params={"limit": 1}, timeout=5)
    first.raise_for_status()
    page = first.json()
    second = requests.get(
        endpoint,
        params={"limit": 1, "offset": 1},
        timeout=5,
    )
    second.raise_for_status()
    following = second.json()
    assert {
        "ids": [item["id"] for item in page["items"] + following["items"]],
        "count": following["count"],
    } == {
        "ids": [parish.pk for parish in parishes],
        "count": 2,
    }
