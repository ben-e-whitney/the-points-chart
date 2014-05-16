from django.db import models

# Create your models here.

class Chore(models.Model):
    short_name = models.CharField(max_length=2**6)
    short_description = models.TextField()
    point_value = models.PositiveSmallIntegerField()
    start_time = models.TimeField()
    end_time   = models.TimeField()

# Bad name.
class ChoreInstance(models.Model):
    chore = models.ForeignKey('Chore')
    date = models.DateField()
    signed_up = models.ForeignKey('Cooper', related_name='chore_signed_up')
    signed_up_datetime = models.DateTimeField()
    signed_off = models.ForeignKey('Cooper', related_name='chore_signed_off')
    signed_off_datetime = models.DateTimeField()
    voided = models.BooleanField()
    voided_datetime = models.DateTimeField()

class Cooper(models.Model):
    full_name = models.CharField(max_length=2**6)
