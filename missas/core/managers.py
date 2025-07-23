from django.db import models
from django.db.models import Case, Count, When


class CityQuerySet(models.QuerySet):
    def annotate_number_of_schedules(self):
        return self.annotate(number_of_schedules=Count("parishes__schedules"))

    def annotate_has_schedules(self):
        return self.annotate_number_of_schedules().annotate(
            has_schedules=Case(
                When(number_of_schedules__gt=0, then=True),
                default=False,
                output_field=models.BooleanField(),
            )
        )


class ScheduleQuerySet(models.QuerySet):
    def filter_verified(self):
        return self.filter(verified_at__isnull=False)
