import json
from collections import defaultdict
from textwrap import dedent
from urllib.parse import quote_plus

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

from missas.core.facades.google_maps import get_location_by_name, get_schedule_address
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

admin.site.register(Source)
admin.site.register(User, UserAdmin)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "maps_link")
    ordering = ("name",)
    search_fields = ("name", "address")

    def get_fields(self, request, obj=None):
        if obj:
            return (
                "name",
                "address",
                "google_maps_place_id",
                "maps_link",
                "formatted_google_maps_response",
            )
        return ("name",)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return (
                "address",
                "google_maps_place_id",
                "maps_link",
                "formatted_google_maps_response",
            )
        return ()

    def save_model(self, request, obj, form, change):
        if not change:
            try:
                location_data = get_location_by_name(obj.name)

                if location_data is None:
                    from django.contrib import messages

                    messages.error(
                        request,
                        f"Não foi possível encontrar localização para '{obj.name}'. "
                        "Por favor, tente com um nome mais específico.",
                    )
                    request._location_save_failed = True
                    return

                obj.name = location_data["name"]
                obj.address = location_data["address"]
                obj.google_maps_response = location_data["full_response"]
                obj.google_maps_place_id = location_data["place_id"]

            except ValueError as e:
                from django.contrib import messages

                messages.error(request, str(e))
                request._location_save_failed = True
                return

        super().save_model(request, obj, form, change)

    def response_add(self, request, obj, post_url_continue=None):
        if hasattr(request, "_location_save_failed") and request._location_save_failed:
            from django.http import HttpResponseRedirect
            from django.urls import reverse

            return HttpResponseRedirect(reverse("admin:core_location_add"))
        return super().response_add(request, obj, post_url_continue)

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
    list_display = ("whatsapp_link",)
    ordering = ("whatsapp",)

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


@admin.register(Parish)
class ParishAdmin(admin.ModelAdmin):
    autocomplete_fields = ("city",)
    list_display = ("name", "city", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "city__name", "slug")


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    autocomplete_fields = ("parish",)
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
    actions = ["create_locations_from_addresses"]

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


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ("name", "short_name", "slug")
    ordering = ("name",)
    search_fields = ("name", "short_name", "slug")
