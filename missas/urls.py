from django.contrib import admin
from django.urls import path

from missas.core import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.index, name="index"),
    path("<slug:state>/<slug:city>/", views.by_city, name="by_city"),
    path("<slug:state>/", views.cities_by_state, name="cities_by_state"),
    path("horarios/<str:id>/", views.fix_schedule, name="fix_schedule"),
]
