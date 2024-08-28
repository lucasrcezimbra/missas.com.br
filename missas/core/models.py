from django.contrib.auth.models import AbstractUser
from django.db import models  # noqa


class User(AbstractUser):
    pass


class State(models.Model):
    name = models.CharField(max_length=254)
    short_name = models.CharField(max_length=2)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class City(models.Model):
    name = models.CharField(max_length=254)
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="cities")
    slug = models.SlugField()

    class Meta:
        unique_together = ("slug", "state")

    def __str__(self):
        return self.name


class Parish(models.Model):
    name = models.CharField(max_length=254)
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="parishes")
    slug = models.SlugField(max_length=254)

    class Meta:
        unique_together = ("slug", "city")

    def __str__(self):
        return self.name


class Source(models.Model):
    class Type(models.TextChoices):
        SITE = ("site", "Site")

    type = models.CharField(choices=Type.choices, default=Type.SITE)
    link = models.URLField(null=True, blank=True)
    description = models.TextField()

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

    parish = models.ForeignKey(
        Parish, on_delete=models.CASCADE, related_name="schedules"
    )
    day = models.IntegerField(choices=Day.choices)
    start_time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True)
    type = models.CharField(choices=Type.choices, default=Type.MASS)
    source = models.ForeignKey(Source, on_delete=models.RESTRICT)
    observation = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ("parish", "day", "start_time")

    def __str__(self):
        if self.end_time:
            return f"{self.get_day_display()} {self.start_time} - {self.end_time} at {self.parish}"
        else:
            return f"{self.get_day_display()} {self.start_time} at {self.parish}"
