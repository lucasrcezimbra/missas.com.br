from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("<slug:state>/<slug:city>/", views.by_city, name="by_city"),
    path("parish/<slug:parish>/", views.by_parish, name="by_parish"),
    path("parish/<slug:parish>/schedules/", views.by_parish, name="by_parish"),
    path("<slug:state>/", views.cities_by_state, name="cities_by_state"),
    path("create_contact/", views.create_contact, name="create_contact"),
]
