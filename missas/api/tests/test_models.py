import pytest
from model_bakery import baker

from missas.api.models import WhatsAppParish
from missas.core.models import Contact, Parish


@pytest.mark.django_db
def test_query_returns_whatsapp_parishes_in_id_order():
    first = baker.make(Parish)
    second = baker.make(Parish)
    baker.make(Contact, parish=second, whatsapp="+5511999990002")
    baker.make(Contact, parish=first, whatsapp="+5511999990001")
    baker.make(
        Contact, parish=baker.make(Parish), whatsapp="\t\n ", phone="+5511999990003"
    )
    baker.make(Parish)
    assert list(WhatsAppParish.objects.for_api()) == [first, second]
