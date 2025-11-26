from django.contrib import admin
from django.urls import path

from missas.core import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.index, name="index"),
    path("contatos/", views.create_contact, name="create_contact"),
    path("proximas/", views.nearby_schedules, name="nearby_schedules"),
    path(
        "<slug:state>/<slug:city>/<slug:parish>/",
        views.parish_detail,
        name="parish_detail",
    ),
    path("<slug:state>/<slug:city>/", views.by_city, name="by_city"),
    path("<slug:state>/", views.cities_by_state, name="cities_by_state"),
]
