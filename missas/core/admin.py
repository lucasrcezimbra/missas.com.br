from django.contrib import admin  # noqa
from django.contrib.auth.admin import UserAdmin

from missas.core.models import City, State, User, Parish, Schedule

admin.site.register(User, UserAdmin)


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("name", "state", "slug")
    search_fields = ("name", "state__name", "slug")
    ordering = ("name",)


@admin.register(Parish)
class ParishAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "slug")
    search_fields = ("name", "city__name", "slug")
    autocomplete_fields = ("city",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ("parish", "type", "day", "start_time")
    search_fields = ("parish__name", "day", "start_time")
    autocomplete_fields = ("parish",)


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ("name", "short_name", "slug")
    search_fields = ("name", "short_name", "slug")
    ordering = ("name",)
