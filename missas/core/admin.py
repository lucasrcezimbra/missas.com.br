from textwrap import dedent
from urllib.parse import quote_plus

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

from missas.core.models import (
    City,
    Contact,
    ContactRequest,
    Parish,
    Schedule,
    Source,
    State,
    User,
)

admin.site.register(Source)
admin.site.register(User, UserAdmin)


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
        "location",
        "observation",
        "verified_at",
    )
    list_filter = (
        ("type", admin.ChoicesFieldListFilter),
        ("day", admin.ChoicesFieldListFilter),
        ("verified_at", admin.EmptyFieldListFilter),
        ("observation", admin.EmptyFieldListFilter),
    )
    search_fields = ("parish__name", "day", "start_time")


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ("name", "short_name", "slug")
    ordering = ("name",)
    search_fields = ("name", "short_name", "slug")
