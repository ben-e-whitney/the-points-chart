from django.db import models

# Create your models here.

import timezone_field

class Coop(models.Model):
    short_name = models.CharField(max_length=2**6)
    short_description = models.TextField()
    email_prefix = models.CharField(default='[Points]')
    time_zone = timezone_field.TimeZoneField()
