from django.db import models

# Create your models here.

import chores.models

# TODO: not sure whether these being so skimpy is a good or bad sign.

class StewardshipSkeleton(chores.models.Skeleton):
    STEWARDSHIP = 'STEW'
    SPECIAL_POINTS = 'SPEC'
    LOAN = 'LOAN'
    CATEGORY_CHOICES = (
        (STEWARDSHIP, 'Stewardship'),
        (SPECIAL_POINTS, 'Special Points'),
        (LOAN, 'Loan')
    )
    category = models.CharField(max_length=4, choices=CATEGORY_CHOICES,
                                default=STEWARDSHIP)
    # Per cycle.
    point_value = models.PositiveSmallIntegerField()

class Stewardship(chores.models.Timecard):
    skeleton = models.ForeignKey(StewardshipSkeleton,
                                 related_name='stewardship')

class BenefitChangeSkeleton(chores.models.Skeleton):
    note = models.TextField()

# For these objects, changes are made for the cycle(s) spanning the date range.
# For example, if a user is marked out for two days, then their load will be
# reduced by the appropriate fraction of the total points for the cycle(s) (not
# days) during which they were absent.
class Absence(chores.models.Timecard):
    skeleton = models.ForeignKey(BenefitChangeSkeleton, related_name='absence')
    # TODO: Superfluous. Use `self.start_date` and `self.stop_date` instead.
    days_gone = models.PositiveSmallIntegerField()

class ShareChange(chores.models.Timecard):
    skeleton = models.ForeignKey(BenefitChangeSkeleton,
                                 related_name='share_change')
    fraction_change = models.DecimalField(max_digits=3, decimal_places=2)
