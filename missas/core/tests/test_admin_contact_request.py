import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from model_bakery import baker

from missas.core.admin import ContactRequestAdmin
from missas.core.models import ContactRequest

User = get_user_model()


@pytest.fixture
def admin_user():
    return baker.make(User, is_staff=True, is_superuser=True)


@pytest.fixture
def contact_request_admin():
    return ContactRequestAdmin(ContactRequest, AdminSite())


@pytest.fixture
def request_factory():
    return RequestFactory()


@pytest.mark.django_db
class TestContactRequestAdmin:
    def test_list_display_includes_created_at(self, contact_request_admin):
        assert "created_at" in contact_request_admin.list_display

    def test_list_display_includes_is_archived(self, contact_request_admin):
        assert "is_archived" in contact_request_admin.list_display

    def test_list_filter_includes_is_archived(self, contact_request_admin):
        assert "is_archived" in contact_request_admin.list_filter

    def test_ordering_by_created_at_desc(self, contact_request_admin):
        assert contact_request_admin.ordering == ("-created_at",)

    def test_archive_action_exists(self, contact_request_admin):
        assert "archive_contact_requests" in contact_request_admin.actions


@pytest.mark.django_db
class TestArchiveAction:
    def test_archive_single_contact_request(
        self, contact_request_admin, request_factory, admin_user, mocker
    ):
        contact_request = baker.make(ContactRequest, is_archived=False)
        request = request_factory.get("/admin/core/contactrequest/")
        request.user = admin_user
        queryset = ContactRequest.objects.filter(pk=contact_request.pk)

        mock_message_user = mocker.patch.object(contact_request_admin, "message_user")
        contact_request_admin.archive_contact_requests(request, queryset)

        contact_request.refresh_from_db()
        assert contact_request.is_archived is True
        mock_message_user.assert_called_once()

    def test_archive_multiple_contact_requests(
        self, contact_request_admin, request_factory, admin_user, mocker
    ):
        contact_requests = baker.make(ContactRequest, is_archived=False, _quantity=3)
        request = request_factory.get("/admin/core/contactrequest/")
        request.user = admin_user
        queryset = ContactRequest.objects.filter(
            pk__in=[cr.pk for cr in contact_requests]
        )

        mock_message_user = mocker.patch.object(contact_request_admin, "message_user")
        contact_request_admin.archive_contact_requests(request, queryset)

        for contact_request in contact_requests:
            contact_request.refresh_from_db()
            assert contact_request.is_archived is True
        mock_message_user.assert_called_once()

    def test_archive_already_archived_contact_request(
        self, contact_request_admin, request_factory, admin_user, mocker
    ):
        contact_request = baker.make(ContactRequest, is_archived=True)
        request = request_factory.get("/admin/core/contactrequest/")
        request.user = admin_user
        queryset = ContactRequest.objects.filter(pk=contact_request.pk)

        mock_message_user = mocker.patch.object(contact_request_admin, "message_user")
        contact_request_admin.archive_contact_requests(request, queryset)

        contact_request.refresh_from_db()
        assert contact_request.is_archived is True
        mock_message_user.assert_called_once()
