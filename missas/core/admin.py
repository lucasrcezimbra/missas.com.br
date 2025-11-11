import json
from collections import defaultdict
from textwrap import dedent
from urllib.parse import quote_plus

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.shortcuts import redirect, render
from django.urls import path
from django.utils.html import format_html

from missas.core.facades.google_maps import (
    get_schedule_address_options,
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

admin.site.register(Source)
admin.site.register(User, UserAdmin)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "maps_link")
    ordering = ("name",)
    readonly_fields = (
        "google_maps_place_id",
        "maps_link",
        "formatted_google_maps_response",
    )
    search_fields = ("name", "address")

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

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "select-location/",
                self.admin_site.admin_view(self.select_location_view),
                name="schedule_select_location",
            ),
        ]
        return custom_urls + urls

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

    def select_location_view(self, request):
        if request.method == "POST":
            selected_option_idx = int(request.POST.get("selected_option"))
            parish_id = int(request.POST.get("parish_id"))
            location_name = request.POST.get("location_name")
            schedule_ids = request.POST.get("schedule_ids").split(",")

            # Retrieve the stored options from session
            session_key = f"location_options_{parish_id}_{location_name}"
            options = request.session.get(session_key)

            if not options:
                self.message_user(
                    request,
                    "Sessão expirou. Por favor, tente novamente.",
                    level="error",
                )
                return redirect("admin:core_schedule_changelist")

            selected_option = options[selected_option_idx]

            # Create or get the location
            location, _ = Location.objects.get_or_create(
                name=selected_option["name"],
                address=selected_option["address"],
                defaults={
                    "google_maps_response": {"results": [selected_option]},
                    "google_maps_place_id": selected_option["place_id"],
                },
            )

            # Update schedules
            schedules = Schedule.objects.filter(id__in=schedule_ids)
            for schedule in schedules:
                schedule.location = location
            Schedule.objects.bulk_update(schedules, ["location"])

            # Clean up session
            del request.session[session_key]

            self.message_user(
                request,
                f"Sucesso: {len(schedule_ids)} horário(s) atualizado(s) com localização {location.name}.",
                level="success",
            )
            return redirect("admin:core_schedule_changelist")

        # GET request - should not happen, redirect to changelist
        return redirect("admin:core_schedule_changelist")

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

        # Process each unique parish-location combination
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
                # Use the new function that returns all options
                address_options = get_schedule_address_options(first_schedule)

                if address_options is None:
                    parish_name = first_schedule.parish.name
                    self.message_user(
                        request,
                        f"Aviso: Não foi possível obter endereço para {parish_name} - {location_name}",
                        level="warning",
                    )
                    total_failed += len(schedules)
                    continue

                if len(address_options) > 1:
                    # Multiple results found - store in session and show selection page
                    session_key = f"location_options_{parish_id}_{location_name}"
                    request.session[session_key] = address_options

                    schedule_ids = ",".join(str(s.id) for s in schedules)

                    context = {
                        "options": address_options,
                        "parish_id": parish_id,
                        "parish_name": first_schedule.parish.name,
                        "location_name": location_name,
                        "schedule_count": len(schedules),
                        "schedule_ids": schedule_ids,
                        "opts": self.model._meta,
                        "has_view_permission": self.has_view_permission(request),
                    }
                    return render(request, "admin/select_location.html", context)

                # Single result - create location directly
                address_data = address_options[0]
                location, _ = Location.objects.get_or_create(
                    name=address_data["name"],
                    address=address_data["address"],
                    defaults={
                        "google_maps_response": {"results": [address_data]},
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
