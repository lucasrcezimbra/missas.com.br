from unittest.mock import Mock, patch

import pytest
from django import forms
from django.contrib.admin.sites import AdminSite
from model_bakery import baker

from missas.core.admin import LocationAdmin, LocationAdminForm
from missas.core.models import Location


class TestLocationAdminForm:
    @pytest.mark.django_db
    def test_form_includes_google_maps_url_field(self):
        form = LocationAdminForm()
        assert "google_maps_url" in form.fields
        assert isinstance(form.fields["google_maps_url"], forms.URLField)

    @pytest.mark.django_db
    def test_google_maps_url_not_required(self):
        form = LocationAdminForm()
        assert form.fields["google_maps_url"].required is False

    @pytest.mark.django_db
    def test_google_maps_url_hidden_for_existing_instances(self):
        location = baker.make(Location)
        form = LocationAdminForm(instance=location)
        assert isinstance(form.fields["google_maps_url"].widget, forms.HiddenInput)

    @pytest.mark.django_db
    @patch("missas.core.admin.get_place_from_url")
    def test_clean_populates_fields_from_google_maps_url(self, mock_get_place):
        mock_get_place.return_value = {
            "name": "Igreja Matriz",
            "address": "Rua Principal, 123, Natal, RN",
            "full_response": {"status": "OK", "result": {}},
            "place_id": "ChIJtest123",
            "latitude": -5.795000,
            "longitude": -35.211000,
        }

        form_data = {
            "google_maps_url": "https://maps.app.goo.gl/test123",
        }
        form = LocationAdminForm(data=form_data)

        is_valid = form.is_valid()
        assert is_valid, form.errors

        assert form.cleaned_data["name"] == "Igreja Matriz"
        assert form.cleaned_data["address"] == "Rua Principal, 123, Natal, RN"
        assert form.cleaned_data["google_maps_place_id"] == "ChIJtest123"
        assert form.cleaned_data["latitude"] == -5.795000
        assert form.cleaned_data["longitude"] == -35.211000

    @pytest.mark.django_db
    @patch("missas.core.admin.get_place_from_url")
    def test_clean_raises_error_when_place_not_found(self, mock_get_place):
        mock_get_place.return_value = None

        form_data = {
            "google_maps_url": "https://maps.app.goo.gl/invalid",
        }
        form = LocationAdminForm(data=form_data)

        assert not form.is_valid()
        assert "Não foi possível obter informações do local" in str(form.errors)

    @pytest.mark.django_db
    @patch("missas.core.admin.get_place_from_url")
    def test_clean_raises_error_on_invalid_url(self, mock_get_place):
        mock_get_place.side_effect = ValueError("Invalid URL format")

        form_data = {
            "google_maps_url": "https://maps.app.goo.gl/invalid",
        }
        form = LocationAdminForm(data=form_data)

        assert not form.is_valid()
        assert "Erro ao processar a URL do Google Maps" in str(form.errors)


class TestLocationAdmin:
    def test_uses_custom_form(self):
        admin = LocationAdmin(Location, AdminSite())
        assert admin.form == LocationAdminForm

    def test_list_display_includes_maps_link(self):
        admin = LocationAdmin(Location, AdminSite())
        assert "maps_link" in admin.list_display
        assert "name" in admin.list_display
        assert "address" in admin.list_display

    def test_get_fields_for_new_instance_includes_google_maps_url_first(self):
        admin = LocationAdmin(Location, AdminSite())
        request = Mock()
        fields = admin.get_fields(request, obj=None)
        assert fields[0] == "google_maps_url"

    def test_get_fields_for_existing_instance_excludes_google_maps_url(self):
        admin = LocationAdmin(Location, AdminSite())
        location = baker.prepare(Location)
        request = Mock()
        fields = admin.get_fields(request, obj=location)
        assert "google_maps_url" not in fields
