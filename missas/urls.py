from django.contrib import admin
from django.urls import path

from missas.core import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.index, name="index"),
    path("contatos/", views.create_contact, name="create_contact"),
    path("brasil/", views.states_brazil, name="states_brazil"),
    path("<slug:state>/<slug:city>/", views.by_city, name="by_city"),
    path("<slug:state>/", views.cities_by_state, name="cities_by_state"),
]
