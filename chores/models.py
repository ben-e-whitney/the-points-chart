from django.db import models

# Create your models here.

from django.contrib.auth.models import User, Group

class Chore(models.Model):
    short_name = models.CharField(max_length=2**6)
    short_description = models.TextField()
    point_value = models.PositiveSmallIntegerField()
    start_time = models.TimeField()
    end_time   = models.TimeField()
    coop = models.ForeignKey(Group, related_name='chore')
    def __str__(self):
        return '{sn} at {co}'.format(sn=self.short_name,
                                     co=self.coop.name)

# Bad name.
class ChoreInstance(models.Model):
    chore = models.ForeignKey('Chore', related_name='instance')
    date = models.DateField()
    signed_up  = models.BooleanField()
    signed_off = models.BooleanField()
    voided     = models.BooleanField()

    who_signed_up  = models.ForeignKey(User, null=True, blank=True,
                                  related_name='chore_signed_up')
    who_signed_off = models.ForeignKey(User, null=True, blank=True,
                                   related_name='chore_signed_off')
    who_voided     = models.ForeignKey(User, null=True, blank=True,
                                   related_name='chore_voided')

    when_signed_up  = models.DateTimeField(null=True, blank=True)
    when_signed_off = models.DateTimeField(null=True, blank=True)
    when_voided     = models.DateTimeField(null=True, blank=True)
    def __str__(self):
        return '{cn} on {da} at {co}'.format(cn=self.chore.short_name,
                                 da=self.date, co=self.chore.coop.name)
