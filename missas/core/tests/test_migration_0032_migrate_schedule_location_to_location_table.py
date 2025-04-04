import importlib

import pytest
from django.utils.text import slugify
from model_bakery import baker
from pytest_django.asserts import assertQuerySetEqual

app_name = "core"
migration_name = "0032_migrate_schedule_location_to_location_table"
migration_full_name = (app_name, migration_name)
migration_module = importlib.import_module("missas.core.migrations." + migration_name)
Migration = migration_module.Migration


@pytest.mark.django_db
def test_empty_before(migrator):
    old_state = migrator.apply_initial_migration(Migration.dependencies[0])

    OldLocation = old_state.apps.get_model(app_name, "Location")

    assert OldLocation.objects.exists() is False


@pytest.mark.django_db
def test_create_location(migrator):
    old_state = migrator.apply_initial_migration(Migration.dependencies[0])
    OldSchedule = old_state.apps.get_model(app_name, "Schedule")
    schedule = baker.make(OldSchedule, location="Main Church", parish__slug='parish-1')

    new_state = migrator.apply_tested_migration(migration_full_name)

    NewLocation = new_state.apps.get_model(app_name, "Location")
    NewSchedule = new_state.apps.get_model(app_name, "Schedule")
    schedule = NewSchedule.objects.get(pk=schedule.pk)
    created_location = NewLocation.objects.get()

    assert created_location.city == schedule.parish.city
    assert created_location.name == schedule.location
    assert created_location.parish == schedule.parish
    assert created_location.slug == 'parish-1-main-church'
    assert created_location.schedules.get() == schedule


@pytest.mark.django_db
def test_location_with_multiple_schedules(migrator):
    old_state = migrator.apply_initial_migration(Migration.dependencies[0])
    OldSchedule = old_state.apps.get_model(app_name, "Schedule")
    location_name = "Main Church"
    schedule1 = baker.make(OldSchedule, location=location_name, parish__slug="parish-1")
    baker.make(OldSchedule, location=location_name, parish=schedule1.parish)

    new_state = migrator.apply_tested_migration(migration_full_name)

    NewLocation = new_state.apps.get_model(app_name, "Location")
    NewSchedule = new_state.apps.get_model(app_name, "Schedule")
    schedules = NewSchedule.objects.all()
    parish = schedules[0].parish
    created_location = NewLocation.objects.get()

    assert created_location.city == parish.city
    assert created_location.name == location_name
    assert created_location.parish == parish
    assert created_location.slug == "parish-1-main-church"
    assert created_location.schedules.count() == 2
    assertQuerySetEqual(created_location.schedules.all(), schedules, ordered=False)


@pytest.mark.django_db
def test_multiple_parishes_in_the_same_city_with_the_same_location_name(migrator):
    old_state = migrator.apply_initial_migration(Migration.dependencies[0])
    OldSchedule = old_state.apps.get_model(app_name, "Schedule")
    location_name = "Main Church"
    schedule1 = baker.make(OldSchedule, location=location_name, parish__slug="parish-1")
    schedule2 = baker.make(OldSchedule, location=location_name, parish__city=schedule1.parish.city, parish__slug="parish-2")

    new_state = migrator.apply_tested_migration(migration_full_name)

    NewLocation = new_state.apps.get_model(app_name, "Location")
    locations = NewLocation.objects.all()

    assert NewLocation.objects.count() == 2
    assert {l.slug for l in locations} == {"parish-1-main-church", "parish-2-main-church"}
