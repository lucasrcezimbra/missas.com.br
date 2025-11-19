import json
from collections import defaultdict
from textwrap import dedent
from urllib.parse import quote_plus

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

from missas.core.facades.google_maps import (
    get_location_from_google_maps_url,
    get_schedule_address,
)
from missas.core.models import (
    City,
    Contact,
    ContactRequest,
    Location,
    Parish,
    Schedule,
    Source,
    State,
    User,
)

admin.site.register(User, UserAdmin)


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ("description", "type", "link")
    list_filter = (("type", admin.ChoicesFieldListFilter),)
    search_fields = ("description", "link")


class LocationAdminForm(forms.ModelForm):
    google_maps_url = forms.URLField(
        required=False,
        label="Google Maps URL",
        help_text="Cole a URL do Google Maps (curta ou longa) para preencher automaticamente os campos",
    )

    class Meta:
        model = Location
        fields = "__all__"
        exclude = ["google_maps_place_id"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            if "name" in self.fields:
                self.fields["name"].required = False
            if "address" in self.fields:
                self.fields["address"].required = False
            if "google_maps_response" in self.fields:
                self.fields["google_maps_response"].required = False
            if "latitude" in self.fields:
                self.fields["latitude"].required = False
            if "longitude" in self.fields:
                self.fields["longitude"].required = False

    def clean(self):
        cleaned_data = super().clean()
        google_maps_url = cleaned_data.get("google_maps_url")

        if google_maps_url:
            location_data = get_location_from_google_maps_url(google_maps_url)
            if location_data:
                from decimal import Decimal

                cleaned_data["name"] = location_data["name"]
                cleaned_data["address"] = location_data["address"]
                cleaned_data["google_maps_response"] = location_data["full_response"]
                self._google_maps_place_id = location_data["place_id"]
                cleaned_data["latitude"] = Decimal(str(location_data["latitude"]))
                cleaned_data["longitude"] = Decimal(str(location_data["longitude"]))
            else:
                raise forms.ValidationError(
                    "Não foi possível obter informações da URL do Google Maps. Verifique se a URL está correta."
                )
        else:
            required_fields = [
                "name",
                "address",
                "latitude",
                "longitude",
            ]
            missing_fields = [
                field for field in required_fields if not cleaned_data.get(field)
            ]

            if missing_fields and not self.instance.pk:
                raise forms.ValidationError(
                    "Preencha a URL do Google Maps ou preencha manualmente todos os campos obrigatórios."
                )

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if hasattr(self, "_google_maps_place_id"):
            instance.google_maps_place_id = self._google_maps_place_id
        if commit:
            instance.save()
        return instance


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    form = LocationAdminForm
    list_display = ("name", "address", "latitude", "longitude", "maps_link")
    ordering = ("name",)
    readonly_fields = (
        "google_maps_place_id",
        "maps_link",
        "formatted_google_maps_response",
    )
    search_fields = ("name", "address")

    def get_fields(self, request, obj=None):
        if obj is None:
            return [
                "google_maps_url",
                "name",
                "address",
                "latitude",
                "longitude",
                "google_maps_response",
            ]
        return [
            "name",
            "address",
            "latitude",
            "longitude",
            "google_maps_response",
            "google_maps_place_id",
            "maps_link",
            "formatted_google_maps_response",
        ]

    def formatted_google_maps_response(self, obj):
        if obj.google_maps_response:
            formatted_json = json.dumps(
                obj.google_maps_response, indent=2, ensure_ascii=False
            )
            return format_html(
                '<pre style="padding: 10px; border-radius: 5px; overflow-x: auto;">{}</pre>',
                formatted_json,
            )
        return "-"

    formatted_google_maps_response.short_description = "Google Maps Response"

    def maps_link(self, obj):
        return format_html(
            '<a href="{url}" target="_blank">Ver no Google Maps</a>',
            url=obj.url,
        )

    maps_link.short_description = "Google Maps"


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("name", "state", "slug")
    list_filter = ("state",)
    ordering = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "state__name", "slug")


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    autocomplete_fields = ("parish",)
    list_display = (
        "parish__name",
        "whatsapp_link",
        "instagram",
        "facebook",
        "email",
        "phone",
        "phone2",
    )
    list_filter = (
        ("parish", admin.EmptyFieldListFilter),
        ("phone", admin.EmptyFieldListFilter),
        ("whatsapp", admin.EmptyFieldListFilter),
    )
    ordering = ("parish__name",)

    def whatsapp_link(self, obj):
        message = dedent(
            """\
       Bom dia.

       Aqui é o Lucas do site missas.com.br. Estamos atualizando o nosso site com as informações sobre as paróquias da Arquidiocese de Natal para ajudar os fiéis a encontrar horários de missas e confissões.

       Você poderia me passar os horários de missas e confissões na sua paróquia?

       Desde já obrigado."""
        )
        return format_html(
            '<a href="https://wa.me/{whatsapp}?text={message}" target="_blank">{whatsapp}</a>',
            whatsapp=obj.whatsapp,
            message=quote_plus(message),
        )

    whatsapp_link.short_description = "WhatsApp Link"


@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    list_display = ("whatsapp_link", "created_at", "is_archived")
    list_filter = ("is_archived",)
    ordering = ("-created_at",)
    actions = ["archive_contact_requests"]

    def whatsapp_link(self, obj):
        message = dedent(
            """\
       Bom dia.

       Aqui é o Lucas do site missas.com.br. Somos um site para ajudar os fiéis a encontrar horários de missas e confissões nas paróquias próximas.

       Um usuário do nosso site nos enviou seu contato.

       Você poderia me passar os horários de missas e confissões na sua paróquia?

       Desde já obrigado."""
        )
        return format_html(
            '<a href="https://wa.me/{whatsapp}?text={message}" target="_blank">{whatsapp}</a>',
            whatsapp=obj.whatsapp,
            message=quote_plus(message),
        )

    whatsapp_link.short_description = "WhatsApp Link"

    def archive_contact_requests(self, request, queryset):
        updated = queryset.update(is_archived=True)
        self.message_user(
            request,
            f"{updated} solicitação(ões) de contato arquivada(s) com sucesso.",
            level="success",
        )

    archive_contact_requests.short_description = (
        "Arquivar solicitações de contato selecionadas"
    )


@admin.register(Parish)
class ParishAdmin(admin.ModelAdmin):
    autocomplete_fields = ("city",)
    list_display = ("name", "city", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "city__name", "slug")


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    autocomplete_fields = (
        "location",
        "parish",
    )
    list_display = (
        "parish",
        "type",
        "day",
        "start_time",
        "location_link",
        "location_name",
        "observation",
        "verified_at",
    )
    list_filter = (
        ("type", admin.ChoicesFieldListFilter),
        ("day", admin.ChoicesFieldListFilter),
        ("verified_at", admin.EmptyFieldListFilter),
        ("observation", admin.EmptyFieldListFilter),
        ("location", admin.EmptyFieldListFilter),
    )
    search_fields = ("parish__name", "day", "start_time")
    actions = ["create_locations_from_addresses", "set_locations_from_same_parish"]

    def location_link(self, obj):
        if obj.location:
            from django.urls import reverse

            url = reverse("admin:core_location_change", args=[obj.location.pk])
            return format_html(
                '<a href="{url}">{name}</a>',
                url=url,
                name=obj.location.name,
            )
        return "-"

    location_link.short_description = "Location"

    def create_locations_from_addresses(self, request, queryset):
        schedules_to_process = queryset.filter(location__isnull=True)

        if not schedules_to_process.exists():
            self.message_user(
                request,
                "Nenhum horário sem localização encontrado.",
                level="warning",
            )
            return

        schedules_by_parish_location = defaultdict(list)
        for schedule in schedules_to_process.select_related(
            "parish", "parish__city", "parish__city__state"
        ):
            key = (schedule.parish_id, schedule.location_name)
            schedules_by_parish_location[key].append(schedule)

        total_updated = 0
        total_failed = 0

        for (
            parish_id,
            location_name,
        ), schedules in schedules_by_parish_location.items():
            first_schedule = schedules[0]

            existing_location = (
                Location.objects.filter(
                    schedule__parish_id=parish_id,
                    schedule__location_name=location_name,
                )
                .exclude(schedule__location__isnull=True)
                .first()
            )

            if existing_location:
                for schedule in schedules:
                    schedule.location = existing_location
                Schedule.objects.bulk_update(schedules, ["location"])
                total_updated += len(schedules)
            else:
                try:
                    address_data = get_schedule_address(first_schedule)
                except ValueError:
                    parish_name = first_schedule.parish.name
                    self.message_user(
                        request,
                        f"Aviso: Multiplos endereços encontrados para {parish_name} - {location_name}",
                        level="warning",
                    )
                    total_failed += len(schedules)
                    continue

                if address_data is None:
                    parish_name = first_schedule.parish.name
                    self.message_user(
                        request,
                        f"Aviso: Não foi possível obter endereço para {parish_name} - {location_name}",
                        level="warning",
                    )
                    total_failed += len(schedules)
                    continue

                location, _ = Location.objects.get_or_create(
                    name=address_data["name"],
                    address=address_data["address"],
                    defaults={
                        "google_maps_response": address_data["full_response"],
                        "google_maps_place_id": address_data["place_id"],
                        "latitude": address_data["latitude"],
                        "longitude": address_data["longitude"],
                    },
                )

                for schedule in schedules:
                    schedule.location = location
                Schedule.objects.bulk_update(schedules, ["location"])
                total_updated += len(schedules)

        if total_updated > 0:
            self.message_user(
                request,
                f"Sucesso: {total_updated} horário(s) atualizado(s) com localização.",
                level="success",
            )
        if total_failed > 0:
            self.message_user(
                request,
                f"Aviso: {total_failed} horário(s) não puderam ser processados.",
                level="warning",
            )

    create_locations_from_addresses.short_description = (
        "Criar localizações a partir de endereços"
    )

    def set_locations_from_same_parish(self, request, queryset):
        schedules_to_process = queryset.filter(location__isnull=True)

        if not schedules_to_process.exists():
            self.message_user(
                request,
                "Nenhum horário sem localização encontrado.",
                level="warning",
            )
            return

        schedules_by_parish_location = defaultdict(list)
        for schedule in schedules_to_process.select_related(
            "parish", "parish__city", "parish__city__state"
        ):
            key = (schedule.parish_id, schedule.location_name)
            schedules_by_parish_location[key].append(schedule)

        total_updated = 0
        total_skipped = 0

        for (
            parish_id,
            location_name,
        ), schedules in schedules_by_parish_location.items():
            existing_location = (
                Location.objects.filter(
                    schedule__parish_id=parish_id,
                    schedule__location_name=location_name,
                )
                .exclude(schedule__location__isnull=True)
                .first()
            )

            if existing_location:
                for schedule in schedules:
                    schedule.location = existing_location
                Schedule.objects.bulk_update(schedules, ["location"])
                total_updated += len(schedules)
            else:
                total_skipped += len(schedules)

        if total_updated > 0:
            self.message_user(
                request,
                f"Sucesso: {total_updated} horário(s) atualizado(s) com localização.",
                level="success",
            )
        if total_skipped > 0:
            self.message_user(
                request,
                f"Aviso: {total_skipped} horário(s) não possuem localização correspondente na mesma paróquia.",
                level="warning",
            )

    set_locations_from_same_parish.short_description = (
        "Definir localizações da mesma paróquia"
    )


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ("name", "short_name", "slug")
    ordering = ("name",)
    search_fields = ("name", "short_name", "slug")
