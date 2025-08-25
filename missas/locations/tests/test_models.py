import pytest
from model_bakery import baker

from missas.locations.models import Location, LocationSchedule


@pytest.mark.django_db
def test_can_create_location():
    location = Location.objects.create(
        name="Main Church", slug="main-church", address="Main Street, 123, Natal, RN"
    )
    assert location.name == "Main Church"
    assert location.slug == "main-church"


@pytest.mark.django_db
def test_can_create_location_with_address():
    location = Location.objects.create(
        name="Main Church", slug="main-church", address="Main Street, 123, Natal, RN"
    )
    assert location.address.raw == "Main Street, 123, Natal, RN"
    assert location.name == "Main Church"


@pytest.mark.django_db
def test_can_create_location_with_parish():
    parish = baker.make("core.Parish")
    location = Location.objects.create(
        name="Main Church",
        slug="main-church",
        address="Main Street, 123, Natal, RN",
        parish=parish,
    )
    assert location.parish == parish
    assert location.parish.name == parish.name


@pytest.mark.django_db
def test_can_create_location_without_parish():
    location = Location.objects.create(
        name="Unknown Chapel",
        slug="unknown-chapel",
        address="Unknown Street, 456, Natal, RN",
    )
    assert location.parish is None
    assert location.name == "Unknown Chapel"


@pytest.mark.django_db
def test_location_string_representation():
    parish = baker.make("core.Parish")
    location = Location.objects.create(
        name="Main Church",
        slug="main-church",
        address="Main Street, 123, Natal, RN",
        parish=parish,
    )
    assert str(location) == f"Main Church ({parish.name})"


@pytest.mark.django_db
def test_location_string_representation_without_parish():
    location = Location.objects.create(
        name="Unknown Chapel",
        slug="unknown-chapel",
        address="Unknown Street, 456, Natal, RN",
    )
    assert str(location) == "Unknown Chapel"


@pytest.mark.django_db
def test_can_create_location_schedule():
    location = Location.objects.create(
        name="Main Church", slug="main-church", address="Main Street, 123, Natal, RN"
    )
    schedule = LocationSchedule.objects.create(
        location=location,
        day=LocationSchedule.Day.SUNDAY,
        start_time="07:00",
        type=LocationSchedule.Type.MASS,
    )
    assert schedule.location == location
    assert schedule.day == LocationSchedule.Day.SUNDAY
    assert str(schedule.start_time) == "07:00"


@pytest.mark.django_db
def test_location_schedule_with_end_time():
    location = Location.objects.create(
        name="Main Church", slug="main-church", address="Main Street, 123, Natal, RN"
    )
    schedule = LocationSchedule.objects.create(
        location=location,
        day=LocationSchedule.Day.SUNDAY,
        start_time="07:00",
        end_time="08:00",
        type=LocationSchedule.Type.MASS,
        observation="Sunday mass",
    )
    assert schedule.end_time is not None
    assert str(schedule.end_time) == "08:00"
    assert schedule.observation == "Sunday mass"


@pytest.mark.django_db
def test_location_schedule_string_representation():
    location = Location.objects.create(
        name="Main Church", slug="main-church", address="Main Street, 123, Natal, RN"
    )
    schedule = LocationSchedule.objects.create(
        location=location,
        day=LocationSchedule.Day.SUNDAY,
        start_time="07:00",
        end_time="08:00",
        type=LocationSchedule.Type.MASS,
    )
    assert str(schedule) == "Domingo 07:00 - 08:00 at Main Church"
