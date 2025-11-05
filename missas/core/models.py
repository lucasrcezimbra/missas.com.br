import re

from django.contrib.auth.models import AbstractUser
from django.db import models
from model_utils import FieldTracker
from model_utils.tracker import FieldInstanceTracker

from missas.core.managers import CityQuerySet, ScheduleQuerySet


class MyFieldInstanceTracker(FieldInstanceTracker):
    def changed(self):
        return {
            field: (self.previous(field), self.get_field_value(field))
            for field in self.fields
            if self.has_changed(field)
        }


class MyFieldTracker(FieldTracker):
    tracker_class = MyFieldInstanceTracker


class User(AbstractUser):
    pass


class State(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=254)
    short_name = models.CharField(max_length=2)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class City(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=254)
    slug = models.SlugField()
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="cities")

    objects = CityQuerySet.as_manager()

    class Meta:
        unique_together = ("slug", "state")

    def __str__(self):
        return f"{self.name}/{self.state.short_name}"


class Parish(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="parishes")
    name = models.CharField(max_length=254)
    slug = models.SlugField(max_length=254)

    class Meta:
        unique_together = ("slug", "city")

    def __str__(self):
        return f"{self.name} ({self.city.name}/{self.city.state.short_name})"


class Contact(models.Model):
    email = models.EmailField(blank=True)
    facebook = models.CharField(max_length=256, blank=True)
    instagram = models.CharField(max_length=64, blank=True)
    phone = models.CharField(max_length=16, blank=True)
    phone2 = models.CharField(max_length=16, blank=True)
    whatsapp = models.CharField(max_length=16, blank=True)
    parish = models.OneToOneField(
        Parish, on_delete=models.CASCADE, blank=True, null=True
    )

    def __str__(self):
        return self.whatsapp or self.phone


class ContactRequest(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    whatsapp = models.CharField(max_length=16)

    def clean(self):
        # TODO: tests
        super().clean()
        self.whatsapp = re.sub(r"\D", "", self.whatsapp)
        self.whatsapp = "+" + self.whatsapp

    def __str__(self):
        return self.whatsapp


class Source(models.Model):
    class Type(models.TextChoices):
        SITE = ("site", "Site")
        WHATSAPP = ("whatsapp", "WhatsApp")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    description = models.TextField(blank=True)
    link = models.URLField(null=True, blank=True)
    type = models.CharField(choices=Type.choices, default=Type.SITE)

    def __str__(self):
        return self.description


class Schedule(models.Model):
    class Day(models.IntegerChoices):
        # It's integer to make the ordering easier
        SUNDAY = (0, "Domingo")
        MONDAY = (1, "Segunda-feira")
        TUESDAY = (2, "Terça-feira")
        WEDNESDAY = (3, "Quarta-feira")
        THURSDAY = (4, "Quinta-feira")
        FRIDAY = (5, "Sexta-feira")
        SATURDAY = (6, "Sábado")

    class Type(models.TextChoices):
        MASS = ("mass", "Missa")
        CONFESSION = ("confession", "Confissão")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    day = models.IntegerField(choices=Day.choices)
    location_name = models.CharField(max_length=128, blank=True)
    observation = models.TextField(blank=True, default="")
    parish = models.ForeignKey(
        Parish, on_delete=models.CASCADE, related_name="schedules"
    )
    source = models.ForeignKey(Source, on_delete=models.RESTRICT, blank=True, null=True)
    start_time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True)
    type = models.CharField(choices=Type.choices, default=Type.MASS)
    verified_at = models.DateField(blank=True, null=True)

    objects = ScheduleQuerySet.as_manager()
    tracker = MyFieldTracker()

    class Meta:
        unique_together = ("parish", "day", "start_time")

    def __str__(self):
        if self.end_time:
            return f"{self.get_day_display()} {self.start_time} - {self.end_time} at {self.parish}"
        else:
            return f"{self.get_day_display()} {self.start_time} at {self.parish}"
