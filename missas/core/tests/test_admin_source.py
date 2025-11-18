import pytest
from django.contrib.admin.sites import AdminSite
from model_bakery import baker

from missas.core.admin import SourceAdmin
from missas.core.models import Source


class TestSourceAdmin:
    def test_list_display_includes_link(self):
        admin = SourceAdmin(Source, AdminSite())
        assert "link" in admin.list_display
        assert "description" in admin.list_display
        assert "type" in admin.list_display

    def test_search_fields_includes_link_and_description(self):
        admin = SourceAdmin(Source, AdminSite())
        assert "link" in admin.search_fields
        assert "description" in admin.search_fields

    def test_list_filter_includes_type(self):
        admin = SourceAdmin(Source, AdminSite())
        assert len(admin.list_filter) == 1
        assert admin.list_filter[0][0] == "type"

    @pytest.mark.django_db
    def test_can_create_source_with_link(self):
        source = baker.make(
            Source, description="Test Source", link="https://example.com", type="site"
        )
        assert source.description == "Test Source"
        assert source.link == "https://example.com"
        assert source.type == "site"

    @pytest.mark.django_db
    def test_can_create_source_without_link(self):
        source = baker.make(
            Source, description="WhatsApp Source", link=None, type="whatsapp"
        )
        assert source.description == "WhatsApp Source"
        assert source.link is None
        assert source.type == "whatsapp"
