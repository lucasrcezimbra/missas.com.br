from address.models import AddressField
from django.db import models


class Location(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=254)
    slug = models.SlugField(max_length=254)
    address = AddressField(on_delete=models.CASCADE)
    parish = models.ForeignKey(
        "core.Parish",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="locations",
    )
    description = models.TextField(blank=True)

    class Meta:
        unique_together = ("slug", "parish")

    def __str__(self):
        if self.parish:
            return f"{self.name} ({self.parish.name})"
        return self.name


class LocationSchedule(models.Model):
    class Day(models.IntegerChoices):
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
    location = models.ForeignKey(
        Location, on_delete=models.CASCADE, related_name="schedules"
    )
    day = models.IntegerField(choices=Day.choices)
    start_time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True)
    type = models.CharField(choices=Type.choices, default=Type.MASS)
    observation = models.TextField(blank=True, default="")
    source = models.ForeignKey(
        "core.Source", on_delete=models.RESTRICT, blank=True, null=True
    )
    verified_at = models.DateField(blank=True, null=True)

    class Meta:
        unique_together = ("location", "day", "start_time")

    def __str__(self):
        if self.end_time:
            return f"{self.get_day_display()} {self.start_time} - {self.end_time} at {self.location}"
        else:
            return f"{self.get_day_display()} {self.start_time} at {self.location}"
