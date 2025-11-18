from unittest.mock import Mock, patch

import pytest
from django.contrib.admin.sites import AdminSite
from model_bakery import baker

from missas.core.admin import LocationAdmin, LocationAdminForm
from missas.core.models import Location


class TestLocationAdmin:
    def test_list_display_includes_expected_fields(self):
        admin = LocationAdmin(Location, AdminSite())
        assert "name" in admin.list_display
        assert "address" in admin.list_display
        assert "latitude" in admin.list_display
        assert "longitude" in admin.list_display
        assert "maps_link" in admin.list_display

    def test_readonly_fields_includes_place_id_and_response(self):
        admin = LocationAdmin(Location, AdminSite())
        assert "google_maps_place_id" in admin.readonly_fields
        assert "maps_link" in admin.readonly_fields
        assert "formatted_google_maps_response" in admin.readonly_fields

    def test_search_fields_includes_name_and_address(self):
        admin = LocationAdmin(Location, AdminSite())
        assert "name" in admin.search_fields
        assert "address" in admin.search_fields

    @pytest.mark.django_db
    def test_maps_link_renders_correctly(self):
        location = baker.make(
            Location,
            name="Test Church",
            google_maps_place_id="ChIJ123ABC",
        )
        admin = LocationAdmin(Location, AdminSite())
        html = admin.maps_link(location)
        assert "Ver no Google Maps" in html
        assert "ChIJ123ABC" in html

    @pytest.mark.django_db
    def test_formatted_google_maps_response_shows_json(self):
        location = baker.make(
            Location,
            google_maps_response={"test": "data", "nested": {"key": "value"}},
        )
        admin = LocationAdmin(Location, AdminSite())
        html = admin.formatted_google_maps_response(location)
        assert "test" in html
        assert "data" in html
        assert "<pre" in html

    @pytest.mark.django_db
    def test_formatted_google_maps_response_returns_dash_when_empty(self):
        location = baker.make(Location, google_maps_response={})
        admin = LocationAdmin(Location, AdminSite())
        result = admin.formatted_google_maps_response(location)
        assert result == "-"

    @pytest.mark.django_db
    def test_get_fields_includes_google_maps_url_for_new_objects(self):
        admin = LocationAdmin(Location, AdminSite())
        fields = admin.get_fields(Mock(), obj=None)
        assert "google_maps_url" in fields

    @pytest.mark.django_db
    def test_get_fields_returns_none_for_existing_objects(self):
        admin = LocationAdmin(Location, AdminSite())
        location = baker.make(Location)
        fields = admin.get_fields(Mock(), obj=location)
        assert fields is None


class TestLocationAdminForm:
    @pytest.mark.django_db
    def test_form_has_google_maps_url_field(self):
        form = LocationAdminForm()
        assert "google_maps_url" in form.fields

    @pytest.mark.django_db
    @patch("missas.core.admin.get_location_from_google_maps_url")
    def test_form_populates_fields_from_google_maps_url(self, mock_get_location):
        mock_get_location.return_value = {
            "name": "Igreja Matriz",
            "address": "Rua Principal, 123 - Centro, Natal - RN",
            "full_response": {"status": "OK", "result": {}},
            "place_id": "ChIJ123ABC",
            "latitude": -5.79000000,
            "longitude": -35.21000000,
        }

        form = LocationAdminForm(
            data={
                "google_maps_url": "https://maps.app.goo.gl/test",
            }
        )

        assert form.is_valid(), f"Form errors: {form.errors}"
        assert form.cleaned_data["name"] == "Igreja Matriz"
        assert form.cleaned_data["address"] == "Rua Principal, 123 - Centro, Natal - RN"
        assert float(form.cleaned_data["latitude"]) == -5.79
        assert float(form.cleaned_data["longitude"]) == -35.21

        location = form.save()
        assert location.google_maps_place_id == "ChIJ123ABC"

    @pytest.mark.django_db
    @patch("missas.core.admin.get_location_from_google_maps_url")
    def test_form_raises_validation_error_for_invalid_url(self, mock_get_location):
        mock_get_location.return_value = None

        form = LocationAdminForm(
            data={
                "google_maps_url": "https://maps.app.goo.gl/invalid",
                "name": "",
                "address": "",
            }
        )

        assert not form.is_valid()
        assert "Não foi possível obter informações da URL do Google Maps" in str(
            form.errors
        )

    @pytest.mark.django_db
    def test_form_works_without_google_maps_url(self):

        form = LocationAdminForm(
            data={
                "name": "Manual Entry",
                "address": "Manual Address",
                "google_maps_place_id": "ChIJManual",
                "latitude": "-5.79000000",
                "longitude": "-35.21000000",
                "google_maps_response": "{}",
            }
        )

        assert form.is_valid(), f"Form errors: {form.errors}"
        assert form.cleaned_data["name"] == "Manual Entry"
        assert form.cleaned_data["address"] == "Manual Address"
