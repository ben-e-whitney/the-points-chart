from django.db import models

# Create your models here.

from django.contrib.auth.models import User, Group

class Signature(models.Model):
    who = models.ForeignKey(User, null=True, blank=True,
                            related_name='signature')
    when = models.DateTimeField(null=True, blank=True)
    def __bool__(self):
        return self.who is not None
    def __str__(self):
        if not self:
            return 'empty Signature'
        else:
            return 'Signature of {use} at {dat}'.format(use=self.who,
                                                        dat=self.when)

class Timecard(models.Model):
    start_date = models.DateField()
    stop_date  = models.DateField()
    # TODO: here or elsewhere, look into ForeignKey limit_choices_to feature.
    # See <https://docs.djangoproject.com/en/dev/ref/models/fields/#foreignkey>.
    signed_up  = models.ForeignKey(Signature,
                                   related_name='timecard_signed_up')
    signed_off = models.ForeignKey(Signature,
                                   related_name='timecard_signed_off')
    voided     = models.ForeignKey(Signature,
                                   related_name='timecard_voided')
    def __str__(self):
        person = self.signed_up.who.profile.short_name \
                if self.signed_up else 'no one'
        coop = self.skeleton.coop.name if hasattr(self, 'skeleton') \
            else '<NO CO-OP SET>'
        return '{cn} at {co} with {per} signed up'\
            .format(cn=self.__class__.__name__, co=coop, per=person)

class Skeleton(models.Model):
    class Meta:
        abstract = True
    # TODO: Adding a related name here caused an error. It looks like it was
    # complaining that two different subclasses of this class had the same
    # accessor/related field/something. If you end up needing this you might
    # need to move the ForeignKey statement to the subclasses, or do something
    # like
    #   coop = models.ForeignKey(Group, self.__class__.__name__)
    # which is I think roughly what the default is anyway.
    coop = models.ForeignKey(Group)
    short_name = models.CharField(max_length=2**6)
    short_description = models.TextField()
    def __str__(self):
        return '{sn} Skeleton at {co}'.format(sn=self.short_name,
                                     co=self.coop.name)
class ChoreSkeleton(Skeleton):
    point_value = models.PositiveSmallIntegerField()
    start_time = models.TimeField()
    end_time   = models.TimeField()

class Chore(Timecard):
    skeleton = models.ForeignKey(ChoreSkeleton, related_name='chore')
    def __str__(self):
        return '{cn} on {da} at {co}'.format(cn=self.skeleton.short_name,
                             da=self.start_date, co=self.skeleton.coop.name)
