import pytest
import requests
from model_bakery import baker

from missas.core.models import Contact, Parish


@pytest.mark.parametrize("path", ["/api/v0/docs", "/api/v0/docs/"])
def test_public_api_documentation(live_server, settings, path):
    settings.DEBUG = False
    docs = requests.get(f"{live_server.url}{path}", timeout=5)
    assert docs.status_code == 200
    assert docs.url == f"{live_server.url}/api/v0/docs/"
    assert len(docs.history) == (0 if path.endswith("/") else 1)
    assert "swagger-ui" in docs.text
    assert "/api/v0/openapi.json" in docs.text

    schema = requests.get(f"{live_server.url}/api/v0/openapi.json", timeout=5)
    assert schema.status_code == 200
    operation = schema.json()["paths"]["/api/v0/parishes"]["get"]
    assert {parameter["name"] for parameter in operation["parameters"]} == {
        "limit",
        "offset",
    }
    assert "200" in operation["responses"]


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
