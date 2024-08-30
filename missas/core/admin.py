from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from missas.core.models import City, Parish, Schedule, Source, State, User

admin.site.register(User, UserAdmin)


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("name", "state", "slug")
    ordering = ("name",)
    search_fields = ("name", "state__name", "slug")


@admin.register(Parish)
class ParishAdmin(admin.ModelAdmin):
    autocomplete_fields = ("city",)
    list_display = ("name", "city", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "city__name", "slug")


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    autocomplete_fields = ("parish",)
    list_display = ("parish", "type", "day", "start_time", "verified_at", "observation")
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


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    pass
