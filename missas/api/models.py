from django.db import models

from missas.core.models import Parish


class WhatsAppParishManager(models.Manager):
    def for_api(self):
        return self.filter(contact__whatsapp__regex=r"\S").order_by("pk")


class WhatsAppParish(Parish):
    objects = WhatsAppParishManager()

    class Meta:
        proxy = True
