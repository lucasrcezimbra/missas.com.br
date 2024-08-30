from django.contrib.auth.models import AbstractUser
from django.db import models  # noqa


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

    class Meta:
        unique_together = ("slug", "state")

    def __str__(self):
        return self.name


class Parish(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="parishes")
    name = models.CharField(max_length=254)
    slug = models.SlugField(max_length=254)

    class Meta:
        unique_together = ("slug", "city")

    def __str__(self):
        return self.name


class Source(models.Model):
    class Type(models.TextChoices):
        SITE = ("site", "Site")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    description = models.TextField()
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
    observation = models.TextField(null=True, blank=True)
    parish = models.ForeignKey(
        Parish, on_delete=models.CASCADE, related_name="schedules"
    )
    source = models.ForeignKey(Source, on_delete=models.RESTRICT)
    start_time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True)
    type = models.CharField(choices=Type.choices, default=Type.MASS)

    class Meta:
        unique_together = ("parish", "day", "start_time")

    def __str__(self):
        if self.end_time:
            return f"{self.get_day_display()} {self.start_time} - {self.end_time} at {self.parish}"
        else:
            return f"{self.get_day_display()} {self.start_time} at {self.parish}"
