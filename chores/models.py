from django.db import models

# Create your models here.

class Chore(models.Model):
    short_name = models.CharField(max_length=2**6)
    short_description = models.TextField()
    point_value = models.PositiveSmallIntegerField()
    start_time = models.TimeField()
    end_time   = models.TimeField()
    coop = models.ForeignKey('coops.Coop', related_name='chore')

    def __str__(self):
        return '{sn} at {co}'.format(sn=self.short_name,
                                     co=self.coop.short_name)


# Bad name.
class ChoreInstance(models.Model):
    chore = models.ForeignKey('Chore')
    date = models.DateField()
    signed_up = models.ForeignKey('coops.Cooper', null=True, blank=True,
                                  related_name='chore_signed_up')
    signed_up_datetime = models.DateTimeField(null=True, blank=True)
    signed_off = models.ForeignKey('coops.Cooper', null=True, blank=True,
                                   related_name='chore_signed_off')
    signed_off_datetime = models.DateTimeField(null=True, blank=True)
    voided = models.BooleanField()
    voided_datetime = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return '{cn} on {da} at {co}'.format(cn=self.chore.short_name,
                                 da=self.date, co=self.chore.coop.short_name)
