import pytest
from model_bakery import baker


@pytest.mark.django_db
def test_ok():
    baker.make("core.User")
    assert True
