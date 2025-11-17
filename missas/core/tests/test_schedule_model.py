import pytest
from django.core.exceptions import ValidationError
from model_bakery import baker

from missas.core.models import Schedule


@pytest.mark.django_db
def test_other_type_requires_description():
    schedule = baker.prepare(
        Schedule, type=Schedule.Type.OTHER, other_type_description=""
    )

    with pytest.raises(ValidationError) as exc_info:
        schedule.full_clean()

    assert "other_type_description" in exc_info.value.message_dict
    assert (
        exc_info.value.message_dict["other_type_description"][0]
        == "Este campo é obrigatório quando o tipo é 'Outro'."
    )


@pytest.mark.django_db
def test_other_type_with_description_is_valid():
    schedule = baker.prepare(
        Schedule,
        type=Schedule.Type.OTHER,
        other_type_description="Adoração ao Santíssimo",
    )

    schedule.full_clean()


@pytest.mark.django_db
def test_non_other_type_should_not_have_description():
    schedule = baker.prepare(
        Schedule, type=Schedule.Type.MASS, other_type_description="Something"
    )

    with pytest.raises(ValidationError) as exc_info:
        schedule.full_clean()

    assert "other_type_description" in exc_info.value.message_dict
    assert (
        exc_info.value.message_dict["other_type_description"][0]
        == "Este campo deve estar vazio quando o tipo não é 'Outro'."
    )


@pytest.mark.django_db
def test_mass_type_without_description_is_valid():
    schedule = baker.prepare(
        Schedule, type=Schedule.Type.MASS, other_type_description=""
    )

    schedule.full_clean()


@pytest.mark.django_db
def test_confession_type_without_description_is_valid():
    schedule = baker.prepare(
        Schedule, type=Schedule.Type.CONFESSION, other_type_description=""
    )

    schedule.full_clean()
